import datetime
import random
import httpx
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from database.conexion import (
    async_obtener_o_crear_usuario,
    async_obtener_moneda,
    async_actualizar_saldo,
    async_ejecutar,
    supabase,
)

logger = logging.getLogger(__name__)


# ============ HELPERS DE TIEMPO Y COOLDOWN (UTC & TIMEZONE-AWARE) ============
def parse_utc_timestamp(ts_str: str | None) -> datetime.datetime | None:
    """Parsea una cadena ISO de timestamp y garantiza que sea un objeto datetime con zona horaria UTC."""
    if not ts_str:
        return None
    try:
        clean_str = str(ts_str).strip()
        if clean_str.endswith("Z"):
            clean_str = clean_str[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = dt.astimezone(datetime.timezone.utc)
        return dt
    except Exception as e:
        logger.error(f"Error parseando timestamp '{ts_str}': {e}")
        return None


def _puede_hacer(ultimo_str, cooldown: datetime.timedelta) -> bool:
    """
    Devuelve True si ya pasó el cooldown o si nunca lo hizo (ultimo_str is None).
    Falla de forma segura: si existe un valor pero no se puede parsear o verificar,
    devuelve False para no conceder recompensas no autorizadas.
    """
    if ultimo_str is None:
        return True

    ultimo = parse_utc_timestamp(ultimo_str)
    if ultimo is None:
        # Fallo seguro: error de formato o lectura -> no autorizar
        return False

    ahora = datetime.datetime.now(datetime.timezone.utc)
    return (ahora - ultimo) >= cooldown


def _restante(ultimo_str, cooldown: datetime.timedelta) -> str | None:
    """Devuelve string 'Xh Ym' con el tiempo restante. None si no hay cooldown pendiente."""
    if ultimo_str is None:
        return None

    ultimo = parse_utc_timestamp(ultimo_str)
    if ultimo is None:
        return None

    ahora = datetime.datetime.now(datetime.timezone.utc)
    diff = cooldown - (ahora - ultimo)
    if diff.total_seconds() <= 0:
        return None

    horas = int(diff.total_seconds() // 3600)
    minutos = int((diff.total_seconds() % 3600) // 60)
    return f"{horas}h {minutos}m"


# ============ HELPERS LOCALES ============
async def _perfil_completo(user_id: int, username: str | None):
    """Trae todos los campos del usuario mediante llamadas asíncronas seguras. Crea si no existe."""
    info = await async_obtener_o_crear_usuario(user_id, username)
    clean_username = username or f"user_{user_id}"

    try:
        res = await async_ejecutar(
            supabase.table("usuarios").select("*").eq("telegram_id", user_id)
        )
        if res.data:
            row = res.data[0]
            return {
                "username": row.get("username", clean_username),
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
        logger.error(f"Error en _perfil_completo para user_id {user_id}: {e}")

    return {
        "username": clean_username,
        "balance": info.get("balance", 0),
        "ganadas": 0,
        "perdidas": 0,
        "ultima_recarga": None,
        "ultimo_robo": None,
        "ultimo_daily": None,
        "pollos_ganados": 0,
        "nuevo": info.get("nuevo", False),
    }


# ============ COMANDOS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info = await _perfil_completo(user.id, user.username)
    m = await async_obtener_moneda()

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
    m = await async_obtener_moneda()
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
        info = await _perfil_completo(user.id, user.username)
        m = await async_obtener_moneda()

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
    """
    Comando /daily: Reclama la recompensa diaria cada 24h.
    Utiliza la función RPC atómica 'reclamar_daily' en PostgreSQL para garantizar
    consistencia transaccional y prevenir duplicaciones por concurrencia.
    """
    if not update.effective_user or not update.message:
        return

    user = update.effective_user
    m = await async_obtener_moneda()

    try:
        # 1. Asegurar existencia del usuario (o crear con balance inicial)
        await async_obtener_o_crear_usuario(user.id, user.username)

        # 2. Invocación de la RPC atómica mediante async_ejecutar
        # Parámetro 'p_telegram_id' según la función SQL en PostgreSQL
        res = await async_ejecutar(
            supabase.rpc("reclamar_daily", {"p_telegram_id": user.id})
        )

        resultado = res.data if res else None
        if not isinstance(resultado, dict):
            logger.error(f"Respuesta inesperada de RPC reclamar_daily para {user.id}: {resultado}")
            await update.message.reply_text("❌ No se pudo procesar tu recompensa diaria. Inténtalo más tarde.")
            return

        # 3. Caso: Recompensa concedida exitosamente
        if resultado.get("exito") is True:
            recompensa = resultado.get("recompensa", 0)
            nuevo_saldo = resultado.get("nuevo_saldo", 0)

            # Envío de confirmación protegido
            try:
                await update.message.reply_text(
                    f"🎁 ¡Reclamaste tu bono diario! Ganaste {recompensa} {m}.\n"
                    f"Saldo actual: {nuevo_saldo} {m}"
                )
            except TelegramError as e_tg:
                # Si Telegram falla en el envío, la transacción ya se consolidó en la base de datos.
                # NO se reintenta ni se vuelve a acreditar saldo.
                logger.error(f"Error enviando confirmación de daily a {user.id} tras cobro exitoso: {e_tg}")
            return

        # 4. Caso: Cooldown activo
        if resultado.get("error") == "cooldown_activo":
            segundos = resultado.get("segundos_restantes", 0)
            horas = int(segundos // 3600)
            minutos = int((segundos % 3600) // 60)
            tiempo_str = f" Vuelve en {horas}h {minutos}m." if segundos > 0 else " Vuelve más tarde."
            await update.message.reply_text(f"⏳ Ya reclamaste tu bono diario.{tiempo_str}")
            return

        # 5. Caso: Usuario no encontrado en la base de datos
        if resultado.get("error") == "usuario_no_encontrado":
            logger.warning(f"RPC reclamar_daily reportó usuario_no_encontrado para {user.id}")
            await update.message.reply_text("❌ Perfil no encontrado. Usa /start para inicializar tu cuenta.")
            return

        # 6. Caso: Desbordamiento de saldo (INTEGER)
        if resultado.get("error") == "desbordamiento_saldo":
            logger.error(f"Riesgo de desbordamiento de INTEGER en balance para {user.id}")
            await update.message.reply_text("❌ Has alcanzado el límite máximo de saldo.")
            return

        # 7. Otros errores controlados
        err_code = resultado.get("error", "desconocido")
        logger.error(f"Error devuelto por reclamar_daily para {user.id}: {err_code}")
        await update.message.reply_text("❌ Ocurrió un error al procesar tu bono diario.")

    except Exception as e:
        # Error de conexión, timeout o indisponibilidad de la base de datos.
        # No reintentar automáticamente para evitar duplicaciones si el commit fue exitoso.
        logger.error(f"Error de base de datos en daily para {user.id}: {e}")
        try:
            await update.message.reply_text("❌ No se pudo conectar con la base de datos. Inténtalo más tarde.")
        except Exception:
            pass


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = await async_ejecutar(
            supabase.table("usuarios")
            .select("username, balance")
            .order("balance", desc=True)
            .limit(10)
        )

        if not res.data:
            await update.message.reply_text("Aún no hay usuarios en el ranking.")
            return

        m = await async_obtener_moneda()
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
