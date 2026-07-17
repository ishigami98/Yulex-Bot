import time
from telegram import Update
from telegram.ext import ContextTypes

# Diccionario global en memoria
afk_data = {}

async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = " ".join(context.args) if context.args else "Sin motivo."
    
    afk_data[user.id] = {
        "reason": reason,
        "time": time.time(),
        "name": user.first_name
    }
    await update.message.reply_text(f"✨ {user.first_name} ahora está AFK: {reason}")

async def check_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.effective_user

    # 1. Si el usuario escribe "brb", lo ponemos AFK automáticamente
    if text.startswith("brb"):
        context.args = update.message.text.split(" ", 1)[1:] if " " in update.message.text else []
        await set_afk(update, context)
        return

    # 2. Si el usuario que ESTABA afk escribe cualquier otra cosa, le quitamos el AFK
    if user.id in afk_data:
        afk_data.pop(user.id)
        await update.message.reply_text(f"👋 {user.first_name} ha vuelto.")
        return

    # 3. Si alguien responde a un mensaje de un usuario AFK
    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        if replied_user and replied_user.id in afk_data:
            data = afk_data[replied_user.id]
            minutes = int((time.time() - data["time"]) / 60)
            await update.message.reply_text(
                f"💤 {replied_user.first_name} está AFK hace {minutes} minutos.\n"
                f"Razón: {data['reason']}"
            )