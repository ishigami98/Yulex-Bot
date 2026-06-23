import random

async def abrazo(update, context):
    user = update.effective_user.first_name
    target = " ".join(context.args) if context.args else "a alguien"
    await update.message.reply_text(f"🤗 {user} le ha dado un abrazo tierno a {target}!")

async def beso(update, context):
    target = " ".join(context.args) if context.args else "a alguien"
    await update.message.reply_text(f"😘 {update.effective_user.first_name} le da un beso a {target}.")

async def ship(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /ship nombre1 nombre2")
        return
    porcentaje = random.randint(0, 100)
    await update.message.reply_text(f"💘 {context.args[0]} y {context.args[1]} tienen un {porcentaje}% de compatibilidad.")