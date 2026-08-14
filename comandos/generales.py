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

    # Si acabamos de crearlo, info solo trae balance. Refetch para más campos:
    try:
        res = supabase.table("usuarios").select("*").eq("telegram_id", user_id).execute()
        if res.data:
            row = res.data[0]
            return {
                "username": row.get("username", username),
                "balance": row.get("balance", 0),
                "ganadas": row.get("ganadas", 0),
                "perdidas": row.get("perdidas", 0),
                "ultimo_daily": row.get("ultima_recarga"),
                "nuevo": info.get("nuevo", False),
            }
    except Exception as e:
        logger.error(f"Error en _perfil_completo: {e}")

    return {
        "username": username,
        "balance": info.get("balance", 0),
        "ganadas": 0,
        "perdidas": 0,
        "ultimo_daily": None,
        "nuevo": info.get("nuevo", False),
    }


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
    texto_help = (
        "🤖 <b>Lista de Comandos Disponibles</b> 🤖\n\n"
        "<b>⚙️ Admin / Moderación:</b>\n"
        "🔸 <code>/set_currency</code> - Cambia el símbolo global.\n"
        "🔸 <code>/add_money</code> - Añade dinero.\n\n"
        "💸 <b>Economía:</b> /perfil, /daily, /leaderboard\n"
        "🎲 <b>Juegos:</b> /trabajar, /robar, /ruleta, /cock_fight, /roll, /cat"
    )
    await update.message.reply_text(texto_help, parse_mode="HTML")


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

        ahora = datetime.datetime.utcnow()
        ultimo = info.get("ultimo_daily")

        if ultimo:
            try:
                ultimo_dt = datetime.datetime.fromisoformat(ultimo)
                if (ahora - ultimo_dt) < datetime.timedelta(hours=24):
                    restante = datetime.timedelta(hours=24) - (ahora - ultimo_dt)
                    horas = int(restante.total_seconds() // 3600)
                    minutos = int((restante.total_seconds() % 3600) // 60)
                    await update.message.reply_text(
                        f"⏳ Ya reclamaste tu daily. Vuelve en {horas}h {minutos}m."
                    )
                    return
            except (ValueError, TypeError):
                pass  # fecha corrupta, dejamos reclamar

        recompensa = random.randint(100, 300)
        actualizar_saldo(user.id, recompensa, es_ganancia=True)
        supabase.table("usuarios").update(
            {"ultima_recarga": ahora.isoformat()}
        ).eq("telegram_id", user.id).execute()

        await update.message.reply_text(
            f"🎁 ¡Reclamaste tu daily! Ganaste {recompensa} {m}."
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
