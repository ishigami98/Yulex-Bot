import time
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Diccionario global en memoria
# Estructura: { telegram_id: { "reason": str, "time": float, "name": str, "chat_id": int } }
afk_data = {}


# ============ HELPERS ============
def _set_afk_for(user, reason: str):
    """Marca un usuario como AFK."""
    afk_data[user.id] = {
        "reason": reason,
        "time": time.time(),
        "name": user.first_name,
    }


def _clear_afk(user_id: int):
    """Quita el AFK si existe. Devuelve True si lo estaba."""
    return afk_data.pop(user_id, None) is not None


# ============ COMANDOS ============
async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = " ".join(context.args) if context.args else "Sin motivo."

    # Si ya estaba AFK, actualizamos motivo sin reiniciar el contador
    if user.id in afk_data:
        afk_data[user.id]["reason"] = reason
        await update.message.reply_text(
            f"🔄 {user.first_name} actualizó su estado AFK: {reason}"
        )
        return

    _set_afk_for(user, reason)
    await update.message.reply_text(
        f"✨ {user.first_name} ahora está AFK.\n"
        f"Razón: {reason}\n"
        f"💡 Escribe cualquier cosa para volver."
    )


async def check_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    text_lower = text.lower()
    user = update.effective_user

    # 1. Si el mensaje es "brb" o empieza con "brb "
    stripped = text_lower.strip()
    if stripped == "brb" or stripped.startswith("brb "):
        # Reutilizamos el comando
        reason = text[3:].strip() or "Sin motivo."
        if user.id in afk_data:
            afk_data[user.id]["reason"] = reason
        else:
            _set_afk_for(user, reason)
        await update.message.reply_text(
            f"💤 {user.first_name} ahora está AFK: {reason}"
        )
        return

    # 2. Si el usuario que estaba AFK escribe cualquier otra cosa, le quitamos el AFK
    if user.id in afk_data:
        _clear_afk(user.id)
        await update.message.reply_text(
            f"👋 Bienvenido de vuelta, {user.first_name}!"
        )
        # NO retornamos: podría haber respondido a otro usuario AFK
        # (raro, pero por consistencia)

    # 3. Si alguien menciona a un usuario AFK
    mentioned_ids = set()
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "text_mention" and entity.user:
                mentioned_ids.add(entity.user.id)
            elif entity.type == "mention":
                # No podemos resolver @username a ID sin un lookup extra
                # Lo dejamos como mejora futura
                pass

    # 4. Si alguien responde a un mensaje de un usuario AFK
    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        if replied_user and replied_user.id in afk_data:
            mentioned_ids.add(replied_user.id)

    if mentioned_ids:
        # Mostramos aviso por cada usuario AFK mencionado
        lineas = []
        for uid in mentioned_ids:
            if uid == user.id:
                continue  # no se notifica a sí mismo
            data = afk_data.get(uid)
            if not data:
                continue
            minutos = int((time.time() - data["time"]) / 60)
            if minutos < 1:
                tiempo = "hace menos de 1 minuto"
            elif minutos < 60:
                tiempo = f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
            else:
                horas = minutos // 60
                mins = minutos % 60
                tiempo = f"hace {horas}h {mins}m"
            lineas.append(f"💤 {data['name']} está AFK {tiempo}.\n📝 Razón: {data['reason']}")

        if lineas:
            await update.message.reply_text("\n\n".join(lineas))
