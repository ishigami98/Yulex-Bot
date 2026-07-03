import os
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import actualizar_saldo, obtener_id_por_username, supabase

# ID del creador para permisos absolutos
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
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        await update.message.reply_text("❌ Uso: `/set_currency <símbolo>` o `/set_currency default`")
        return
    
    nuevo_simbolo = "🪙" if context.args[0].lower() == "default" else context.args[0]
    
    # Guardar en Supabase (asumiendo que tienes una tabla de 'config' o similar)
    # Si no tienes tabla, esto es un placeholder.
    await update.message.reply_text(f"✅ Símbolo global cambiado a: {nuevo_simbolo}")

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context): return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/add_money @usuario <cantidad>`")
        return
        
    target_user = context.args[0]
    cantidad = int(context.args[1])
    target_id = obtener_id_por_username(target_user)
    
    if target_id:
        res = supabase.table("usuarios").select("balance").eq("telegram_id", target_id).execute()
        nuevo_saldo = res.data[0]["balance"] + cantidad
        supabase.table("usuarios").update({"balance": nuevo_saldo}).eq("telegram_id", target_id).execute()
        await update.message.reply_text(f"✅ Se añadieron {cantidad} al saldo de {target_user}.")
    else:
        await update.message.reply_text("❌ Usuario no encontrado.")

async def remove_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context): return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/remove_money @usuario <cantidad>`")
        return
        
    target_user = context.args[0]
    cantidad = int(context.args[1])
    target_id = obtener_id_por_username(target_user)
    
    if target_id:
        res = await supabase.table("usuarios").select("balance").eq("telegram_id", target_id).execute()
        nuevo_saldo = max(0, res.data[0]["balance"] - cantidad)
        supabase.table("usuarios").update({"balance": nuevo_saldo}).eq("telegram_id", target_id).execute()
        await update.message.reply_text(f"📉 Se retiraron {cantidad} del saldo de {target_user}.")

async def reset_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No eres administrador.")
        return
    
    # Reset masivo a todos los usuarios
    await supabase.table("usuarios").update({"balance": 0}).neq("telegram_id", 0).execute()
    await update.message.reply_text("🚨 **LA ECONOMÍA HA SIDO REINICIADA**. El saldo de todos se fijó en 0.")

async def reset_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args and await es_administrador(update, context):
        target_user = context.args[0]
        target_id = obtener_id_por_username(target_user)
        if target_id:
            supabase.table("usuarios").update({"balance": 500, "ganadas": 0, "perdidas": 0}).eq("telegram_id", target_id).execute()
            await update.message.reply_text(f"🔄 Se reinició el dinero de {target_user} a 500.")
            return
            
    # Reset propio si no es admin o no hay args
    await supabase.table("usuarios").update({"balance": 500}).eq("telegram_id", user_id).execute()
    await update.message.reply_text("🔄 Has reiniciado tu dinero al balance inicial (500).")
    
async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /give_money <@usuario> <cantidad>")
        return
        
    target_username = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        return
        
    target_id = obtener_id_por_username(target_username)
    if target_id:
        actualizar_saldo(target_id, cantidad, es_ganancia=True)
        await update.message.reply_text(f"✅ Se han enviado {cantidad} a {target_username}.")
    else:
        await update.message.reply_text("❌ Usuario no encontrado.")