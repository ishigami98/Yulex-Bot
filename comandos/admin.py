import os
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import (
    conectar_db, obtener_id_por_username, actualizar_saldo, obtener_moneda
)

CREADOR_ID = int(os.environ.get("CREADOR_ID", 5235708855))

async def es_administrador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == CREADOR_ID:
        return True
    if update.effective_chat.type in ["group", "supergroup"]:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            return True
    return False

async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos de administrador para usar esto.")
        return
    if not context.args:
        await update.message.reply_text("❌ Uso: `/set-currency <símbolo>` o `/set-currency default`")
        return
    nuevo_simbolo = context.args[0]
    if nuevo_simbolo.lower() == "default":
        nuevo_simbolo = "🪙"
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE configuracion SET valor = %s WHERE clave = 'moneda'", (nuevo_simbolo,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Símbolo de moneda cambiado a: {nuevo_simbolo}")

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No eres administrador.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/add-money @usuario <cantidad>`")
        return
    target_user = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Cantidad inválida.")
        return
    target_id = obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text("❌ Usuario no encontrado en el bot.")
        return
    actualizar_saldo(target_id, cantidad, es_ganancia=True)
    m = obtener_moneda()
    await update.message.reply_text(f"✅ Se añadieron {m} {cantidad} al saldo de {target_user}.")

async def remove_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No eres administrador.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/remove-money @usuario <cantidad>`")
        return
    target_user = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Cantidad inválida.")
        return
    target_id = obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return
    actualizar_saldo(target_id, cantidad, es_ganancia=False)
    m = obtener_moneda()
    await update.message.reply_text(f"📉 Se retiraron {m} {cantidad} del saldo de {target_user}.")

async def reset_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No eres administrador.")
        return
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET balance = 0")
    conn.commit()
    conn.close()
    await update.message.reply_text("🚨 **LA ECONOMÍA HA SIDO REINICIADA**. El saldo de todos se fijó en 0.")

async def reset_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args and await es_administrador(update, context):
        target_user = context.args[0]
        target_id = obtener_id_por_username(target_user)
        if target_id:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET balance = 500, ganadas=0, perdidas=0 WHERE telegram_id = %s", (target_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"🔄 Se reinició el dinero de {target_user} a 500.")
            return
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET balance = 500 WHERE telegram_id = %s", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("🔄 Has reiniciado tu dinero al balance inicial (500).")