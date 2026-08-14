import datetime
import random
import httpx
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import obtener_o_crear_usuario, obtener_moneda, actualizar_saldo, supabase

logger = logging.getLogger(__name__)


# ============ HELPERS LOCALES ============
def _perfil_completo(user_id, username):
    """Trae todos los campos del usuario. Crea si no existe."""
    info = obtener_o_crear_usuario(user_id, username)
    username = username or f"user_{user_id}"

    try:
        res = supabase.table("usuarios").select("*").eq("telegram_id", user_id).execute()
        if res.data:
            row = res.data[0]
            return {
                "username": row.get("username", username),
                "balance": row.get("balance", 0),
                "ganadas": row.get("ganadas", 0),
                "perdidas": row.get("perdidas", 0),
                "ultima_recarga": row.get("ultima_recarga"),
                "ultimo_robo": row.get("ultimo_robo"),
                "ultimo_daily": row.get("ultimo_daily"),
                "pollos_ganados": row.get("pollos_ganados", 0),
                "nuevo": info.get("nuevo", False),
            }
    except Exception as e:
        logger.error(f"Error en _perfil_completo: {e}")

    return {
        "username": username,
        "balance": info.get("balance", 0),
        "ganadas": 0,
        "perdidas": 0,
        "ultima_recarga": None,
        "ultimo_robo": None,
        "ultimo_daily": None,
        "pollos_ganados": 0,
        "nuevo": info.get("nuevo", False),
    }


def _puede_hacer(ultimo_str, cooldown):
    """Devuelve True si ya pasó el cooldown (o si nunca lo hizo)."""
    if not ultimo_str:
        return True
    try:
        ultimo = datetime.datetime.fromisoformat(ultimo_str)
        ahora = datetime.datetime.utcnow()
        return (ahora - ultimo) >= cooldown
    except (ValueError, TypeError):
        return True


def _restante(ultimo_str, cooldown):
    """Devuelve string 'Xh Ym' con el tiempo restante. None si no hay cooldown."""
    if not ultimo_str:
        return None
    try:
        ultimo = datetime.datetime.fromisoformat(ultimo_str)
        ahora = datetime.datetime.utcnow()
        diff = cooldown - (ahora - ultimo)
        if diff.total_seconds() <= 0:
            return None
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)
        return f"{horas}h {minutos}m"
    except (ValueError, TypeError):
        return None


# ============ COMANDOS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info = _perfil_completo(user.id, user.username)
    m = obtener_moneda()

    if info["nuevo"]:
        await update.message.reply_text(
            f"👋 ¡Hola {user.first_name}! Bienvenido al CasinoBot.\n"
            f"Te he regalado 500 {m} de bienvenida. Usa /help para ver los comandos."
        )
    else:
        await update.message.reply_text(
            f"¡Hola de nuevo, {user.first_name}! Tu saldo actual es de {info['balance']} {m}."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = obtener_moneda()
    texto = (
        "🤖 <b>Lista de Comandos</b> 🤖\n\n"

        "<b>💼 Economía</b>\n"
        "🔸 <code>/perfil</code> — Ver tu saldo, victorias y derrotas.\n"
        "🔸 <code>/daily</code> — Reclamar tu bono diario (cada 24h).\n"
        "🔸 <code>/leaderboard</code> — Top 10 de los más ricos.\n\n"

        "<b>🎲 Juegos de azar</b>\n"
        f"🔸 <code>/ruleta &lt;cantidad&gt; &lt;color&gt;</code> — Apuesta al rojo, negro o verde. "
        "Verde paga x14, el resto x2.\n"
        f"🔸 <code>/roll &lt;cantidad&gt; &lt;número 1-6&gt;</code> — Adivina el dado. Si aciertas ganas x1.5.\n"
        f"🔸 <code>/cock_fight &lt;cantidad&gt;</code> — Pelea de gallos, ganás x2.\n\n"

        "<b>💸 Trabajo y Crimen</b>\n"
        "🔸 <code>/trabajar</code> — Trabaja y gana monedas (cada 8h).\n"
        "🔸 <code>/crimen</code> — Intenta un crimen, puede salir bien o mal (cada 4h).\n\n"

        "<b>😴 Otros</b>\n"
        "🔸 <code>/afk [razón]</code> — Marcarte como ausente. Vuelve escribiendo cualquier cosa.\n"
        "🔸 <code>/cat</code> — Foto random de un gato.\n"
        "🔸 <code>/help</code> — Muestra este mensaje.\n\n"

        f"<i>La moneda actual es {m}.</i>"
    )
    await update.message.reply_text(texto, parse_mode="HTML")


async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        info = _perfil_completo(user.id, user.username)
        m = obtener_moneda()

        texto = (
            f"👤 <b>Perfil de @{info['username']}</b>\n\n"
            f"💰 Saldo: {info['balance']} {m}\n"
            f"📈 Victorias: {info['ganadas']}\n"
            f"📉 Derrotas: {info['perdidas']}"
        )
        await update.message.reply_text(texto, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error en perfil: {e}")
        await update.message.reply_text("❌ Hubo un error al cargar tu perfil. Inténtalo más tarde.")


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        info = _perfil_completo(user.id, user.username)
        m = obtener_moneda()

        # Cooldown propio: ultimo_daily (24h)
        if not _puede_hacer(info["ultimo_daily"], datetime.timedelta(hours=24)):
            restante = _restante(info["ultimo_daily"], datetime.timedelta(hours=24))
            await update.message.reply_text(
                f"⏳ Ya reclamaste tu daily. Vuelve en {restante}."
            )
            return

        recompensa = random.randint(100, 300)
        nuevo = actualizar_saldo(user.id, recompensa, es_ganancia=True)
        # Escribe en su PROPIA columna, no en ultima_recarga
        supabase.table("usuarios").update(
            {"ultimo_daily": datetime.datetime.utcnow().isoformat()}
        ).eq("telegram_id", user.id).execute()

        await update.message.reply_text(
            f"🎁 ¡Reclamaste tu daily! Ganaste {recompensa} {m}.\n"
            f"Saldo actual: {nuevo} {m}"
        )

    except Exception as e:
        logger.error(f"Error en daily: {e}")
        await update.message.reply_text("❌ Error al reclamar el daily.")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = supabase.table("usuarios") \
            .select("username, balance") \
            .order("balance", desc=True) \
            .limit(10) \
            .execute()

        if not res.data:
            await update.message.reply_text("Aún no hay usuarios en el ranking.")
            return

        m = obtener_moneda()
        lineas = ["🏆 <b>Top 10 más ricos</b> 🏆\n"]
        for i, row in enumerate(res.data, start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            lineas.append(f"{medal} @{row.get('username', '?')} — {row.get('balance', 0)} {m}")

        await update.message.reply_text("\n".join(lineas), parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error en leaderboard: {e}")
        await update.message.reply_text("❌ Error al cargar el ranking.")


async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.thecatapi.com/v1/images/search", timeout=10.0)
            data = r.json()
            if data and isinstance(data, list) and len(data) > 0:
                await update.message.reply_photo(data[0]["url"], caption="Toma un gatito 🐱")
            else:
                await update.message.reply_text("❌ No pude encontrar un gatito, intenta de nuevo.")
    except Exception as e:
        logger.error(f"Error en cat: {e}")
        await update.message.reply_text("❌ Error al buscar el gatito.")
