import random
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database.conexion import obtener_o_crear_usuario, obtener_moneda, actualizar_saldo, conectar_db

# --- LÓGICA DE APUESTA UNIFICADA ---
async def procesar_apuesta(update_obj, context, monto_str, color_usuario):
    # Determinamos si viene de un comando (Update) o un botón (CallbackQuery)
    user_id = update_obj.effective_user.id
    username = update_obj.effective_user.username
    
    info = obtener_o_crear_usuario(user_id, username)
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

    if color_usuario not in ["rojo", "negro"]:
        return "❌ El color debe ser `rojo` o `negro`."

    # Lógica de juego
    resultado_ruleta = random.choice(["rojo", "negro"])
    emoji = "🔴" if resultado_ruleta == "rojo" else "⚫"
    
    if color_usuario == resultado_ruleta:
        actualizar_saldo(user_id, monto, es_ganancia=True)
        return f"🎰 La ruleta cae en... {resultado_ruleta} {emoji}!\n🎉 ¡Ganaste {m} {monto}!"
    else:
        actualizar_saldo(user_id, monto, es_ganancia=False)
        return f"🎰 La ruleta cae en... {resultado_ruleta} {emoji}!\n🤡 Perdiste {m} {monto}."

# --- COMANDO /RULETA ---
async def ruleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 1:
        monto_str = context.args[0].lower()
        keyboard = [
            [
                InlineKeyboardButton("🔴 Rojo", callback_data=f"apuesta_rojo_{monto_str}"),
                InlineKeyboardButton("⚫ Negro", callback_data=f"apuesta_negro_{monto_str}")
            ]
        ]
        await update.message.reply_text(f"Has elegido apostar {monto_str}. ¿A qué color?", reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(context.args) >= 2:
        respuesta = await procesar_apuesta(update, context, context.args[0], context.args[1])
        await update.message.reply_text(respuesta)
    else:
        await update.message.reply_text("❌ Uso: `/ruleta <cantidad> <rojo/negro>` o `/ruleta <cantidad>`")

# --- MANEJADOR DE BOTONES ---
async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, color, monto = query.data.split("_")
    respuesta = await procesar_apuesta(query, context, monto, color)
    
    await query.edit_message_text(text=f"{query.message.text}\n\n{respuesta}")

# ... (mantén tus funciones trabajar, cock_fight y roll aquí abajo)

async def trabajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Obtenemos los datos actuales
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ultima_trabajo FROM usuarios WHERE telegram_id = %s", (user_id,))
    fila = cursor.fetchone()
    
    ahora = datetime.datetime.now()
    if fila and fila[0]:
        ultima_vez = datetime.datetime.fromisoformat(fila[0])
        if (ahora - ultima_vez).total_seconds() < 300: # 300 segundos = 5 minutos
            await update.message.reply_text("⏳ Espera 5 minutos para volver a trabajar.")
            return

    # Si pasa el tiempo, ejecuta el trabajo
    paga = random.randint(300, 600)
    actualizar_saldo(user_id, paga, es_ganancia=True)
    
    # Guarda la nueva hora
    cursor.execute("UPDATE usuarios SET ultima_trabajo = %s WHERE telegram_id = %s", (ahora.isoformat(), user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"💼 Trabajaste y ganaste {paga}.")

async def robar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    obtener_o_crear_usuario(user_id, update.effective_user.username)
    m = obtener_moneda()
    resultado = random.randint(-500, 1000)
    if resultado >= 0:
        actualizar_saldo(user_id, resultado, es_ganancia=True)
        await update.message.reply_text(f"🥷 ¡El atraco funcionó! Robaste {m} {resultado} con éxito.")
    else:
        perdida = abs(resultado)
        actualizar_saldo(user_id, perdida, es_ganancia=False)
        await update.message.reply_text(f"🚓 ¡Te atrapó la policía de camino! Pagaste una fianza de {m} {perdida}.")

async def cock_fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = obtener_o_crear_usuario(user_id, update.effective_user.username)
    m = obtener_moneda()
    if not context.args:
        await update.message.reply_text("❌ Uso: `/cock_fight <apuesta>`")
        return
    try:
        apuesta = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Apuesta inválida.")
        return
    if apuesta <= 0 or info["balance"] < apuesta:
        await update.message.reply_text("❌ Dinero insuficiente o apuesta inválida.")
        return
    probabilidad = min(50 + info["pollos"], 70)
    await update.message.reply_text(f"🐓 Tu gallo va a la arena... (Probabilidad: {probabilidad}%)")
    if random.randint(1, 100) <= probabilidad:
        actualizar_saldo(user_id, apuesta, es_ganancia=True)
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET pollos_ganados = pollos_ganados + 1 WHERE telegram_id = %s", (user_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"🏆 ¡Victoria! Tu gallo ganó. Sumas {m} {apuesta} y tu gallo se vuelve más fuerte.")
    else:
        actualizar_saldo(user_id, apuesta, es_ganancia=False)
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET pollos_ganados = 0 WHERE telegram_id = %s", (user_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"💀 Tu gallo fue derrotado. Perdiste {m} {apuesta} y la racha volvió a 0.")

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        resultado = random.randint(1, 6)
        await update.message.reply_text(f"🎲 Dado clásico (6 caras): **{resultado}**")
        return
    argumento = " ".join(context.args)
    if "," in argumento:
        opciones = [o.strip() for o in argumento.split(",")]
        elegido = random.choice(opciones)
        await update.message.reply_text(f"🔮 El azar seleccionó: **{elegido}**")
    else:
        try:
            caras = int(argumento)
            if caras < 2: raise ValueError
            resultado = random.randint(1, caras)
            await update.message.reply_text(f"🎲 Dado de {caras} caras: **{resultado}**")
        except ValueError:
            await update.message.reply_text("❌ Usa un número de caras válido o separa tus opciones con comas.")