import time
from telegram import Update
from telegram.ext import ContextTypes

# Diccionario: {user_id: {"reason": str, "time": float, "name": str}}
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
    # 1. Si alguien responde a un usuario AFK, avisar
    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        if replied_user.id in afk_data:
            data = afk_data[replied_user.id]
            minutes = int((time.time() - data["time"]) / 60)
            await update.message.reply_text(
                f"💤 {replied_user.first_name} está AFK hace {minutes} minutos.\n"
                f"Razón: {data['reason']}"
            )
    
    # 2. Si el usuario que estaba AFK escribe algo, quitar su estado
    user = update.effective_user
    if user.id in afk_data:
        afk_data.pop(user.id)
        await update.message.reply_text(f"👋 {user.first_name} ha vuelto.")