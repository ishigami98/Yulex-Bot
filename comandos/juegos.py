import random
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import obtener_o_crear_usuario, obtener_moneda, actualizar_saldo, supabase

# --- LÓGICA DE APUESTA UNIFICADA ---
async def procesar_apuesta(update_obj, context, monto_str, color_usuario):
    if hasattr(update_obj, 'from_user'):
        user = update_obj.from_user
    else:
        user = update_obj.effective_user
        
    user_id = user.id
    username = user.username or user.first_name
    
    info = await obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    
    # Validar monto
    if monto_str == "all":
        monto = info["balance"]
    else:
        try:
            monto = int(monto_str)
        except ValueError:
            return "❌ Ingresa una cantidad numérica válida."

    if monto <= 0 or monto > info["balance"]:
        return f"❌ Balance insuficiente. Saldo: {m} {info['balance']}"

    # Lógica de Ruleta
    resultado = random.choice(["rojo", "negro"])
    if resultado == color_usuario.lower():
        await actualizar_saldo(user_id, monto, es_ganancia=True) 
        return f"🎉 ¡Ganaste! Salió {resultado}. Ganaste {m} {monto}."
    else:
        await actualizar_saldo(user_id, monto, es_ganancia=False) 
        return f"💸 Perdiste. Salió {resultado}. Perdiste {m} {monto}."

async def trabajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    res = await supabase.table("usuarios").select("ultima_trabajo").eq("telegram_id", user_id).execute()
    
    ahora = datetime.datetime.now()
    if res.data and res.data[0].get("ultima_trabajo"):
        ultima_vez = datetime.datetime.fromisoformat(res.data[0]["ultima_trabajo"])
        if (ahora - ultima_vez).total_seconds() < 300:
            await update.message.reply_text("⏳ Espera 5 minutos para volver a trabajar.")
            return

    paga = random.randint(300, 600)
    actualizar_saldo(user_id, paga, es_ganancia=True)
    supabase.table("usuarios").update({"ultima_trabajo": ahora.isoformat()}).eq("telegram_id", user_id).execute()
    await update.message.reply_text(f"✅ ¡Has trabajado y ganado {obtener_moneda()} {paga}!")

async def robar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    exito = random.choice([True, False])
    m = obtener_moneda()
    
    if exito:
        botin = random.randint(100, 200)
        actualizar_saldo(user_id, botin, es_ganancia=True)
        await update.message.reply_text(f"💰 ¡Robo exitoso! Ganaste {m} {botin}.")
    else:
        multa = random.randint(50, 150)
        actualizar_saldo(user_id, multa, es_ganancia=False)
        await update.message.reply_text(f"👮‍♂️ ¡Te atraparon! Pagaste {m} {multa} de multa.")

async def ruleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Uso: `/ruleta <cantidad> <rojo/negro>`")
        return
    # Aquí puedes mantener la lógica para mostrar botones si quieres o simplificar a solo comando
    await update.message.reply_text("Has elegido apostar. (Usa los botones si están activos).")

async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, color, monto = query.data.split("_")
    respuesta = await procesar_apuesta(query, context, monto, color)
    await query.edit_message_text(text=f"{query.message.text}\n\n{respuesta}")

async def cock_fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lógica simplificada con el cliente supabase
    user_id = update.effective_user.id
    apuesta = int(context.args[0]) if context.args else 100
    
    if random.random() < 0.6: # 60% win rate
        actualizar_saldo(user_id, apuesta, es_ganancia=True)
        await update.message.reply_text("🏆 ¡Victoria de tu gallo! Has ganado.")
    else:
        actualizar_saldo(update.effective_user.id, apuesta, es_ganancia=False)
        await update.message.reply_text("💀 Tu gallo fue derrotado. Perdiste.")

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = random.randint(1, 6)
    await update.message.reply_text(f"🎲 Resultado: **{resultado}**")