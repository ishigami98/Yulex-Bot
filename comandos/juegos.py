import random
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import obtener_o_crear_usuario, obtener_moneda, actualizar_saldo, conectar_db

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

async def ruleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = obtener_o_crear_usuario(user_id, update.effective_user.username)
    m = obtener_moneda()
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso correcto: `/ruleta <cantidad> <rojo/negro>`")
        return
    monto_str = context.args[0].lower()
    color_usuario = context.args[1].lower()
    if color_usuario not in ["rojo", "negro"]:
        await update.message.reply_text("❌ El color debe ser `rojo` o `negro`.")
        return
    if monto_str == "all":
        monto = info["balance"]
    else:
        try:
            monto = int(monto_str)
        except ValueError:
            await update.message.reply_text("❌ Ingresa una cantidad numérica válida.")
            return
    if monto <= 0 or monto > info["balance"]:
        await update.message.reply_text(f"❌ Balance insuficiente o inválido. Saldo: {m} {info['balance']}")
        return
    opciones = ["rojo", "negro"]
    resultado_ruleta = random.choice(opciones)
    emoji = "🔴" if resultado_ruleta == "rojo" else "⚫"
    if color_usuario == resultado_ruleta:
        actualizar_saldo(user_id, monto, es_ganancia=True)
        await update.message.reply_text(f"🎰 La ruleta cae en... {resultado_ruleta} {emoji}!\n🎉 ¡Ganaste {m} {monto}!")
    else:
        actualizar_saldo(user_id, monto, es_ganancia=False)
        await update.message.reply_text(f"🎰 La ruleta cae en... {resultado_ruleta} {emoji}!\n🤡 Perdiste {m} {monto}.")

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