import datetime
import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import (
    obtener_o_crear_usuario, obtener_moneda, obtener_id_por_username, 
    actualizar_saldo, conectar_db
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    info = obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    if info["nuevo"]:
        await update.message.reply_text(f"👋 ¡Hola {username}! ¡Bienvenido al CasinoBot!\nTe he regalado {m} 500 de bienvenida. ¡Usa /help para ver los comandos!")
    else:
        await update.message.reply_text(f"¡Hola de nuevo, {username}! Tu saldo actual es de {m} {info['balance']}.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = obtener_moneda()
    texto_help = (
        "🤖 **Lista de Comandos Disponibles** 🤖\n\n"
        "**⚙️ Admin / Moderación:**\n"
        "🔸 `/set_currency <simbolo/default>` - Cambia el símbolo global.\n"
        "🔸 `/add_money <@usuario> <cantidad>` - Añade saldo a un miembro.\n"
        "🔸 `/remove_money <@usuario> <cantidad>` - Retira saldo.\n"
        "🔸 `/reset_economy` - Pone el saldo de todos a 0.\n\n"
        "**💸 Economía y Perfil:**\n"
        "🔸 `/start` - Inicia el bot.\n"
        "🔸 `/help` - Muestra esta lista.\n"
        "🔸 `/perfil` - Mira tus estadísticas y dinero.\n"
        "🔸 `/daily` - Monedas gratis cada 24h.\n"
        "🔸 `/give_money <@usuario> <cantidad/all>` - Regala dinero a un amigo.\n"
        "🔸 `/reset_money [@usuario/propio]` - Resetea el saldo.\n"
        "🔸 `/leaderboard` - Ranking de los más ricos.\n\n"
        "**🎲 Juegos y Ocio:**\n"
        "🔸 `/trabajar` - Consigue un empleo temporal.\n"
        "🔸 `/robar` - Intenta un atraco aleatorio.\n"
        "🔸 `/ruleta <cantidad> <rojo/negro>` - Apuesta en el color.\n"
        "🔸 `/cock_fight <apuesta>` - Envía tu pollo a pelear (50%-70% win rate).\n"
        "🔸 `/roll [caras o opciones]` - Tira un dado o elige de una lista.\n"
        "🔸 `/cat` - Envía una foto aleatoria de un gatito."
    )
    await update.message.reply_markdown(texto_help)

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    info = obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    texto_perfil = (
        "👤 **PERFIL DE USUARIO** 👤\n\n"
        f"🔹 **Usuario:** @{username}\n"
        f"🔹 **Saldo Actual:** {m} {info['balance']}\n"
        f"📈 **Monedas Ganadas:** {info['ganadas']}\n"
        f"📉 **Monedas Perdidas:** {info['perdidas']}\n"
        f"🐓 **Victorias de Pollo:** {info['pollos']}"
    )
    await update.message.reply_markdown(texto_perfil)

async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info_origen = obtener_o_crear_usuario(user_id, update.effective_user.username)
    m = obtener_moneda()
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/give_money @usuario <cantidad/all>`")
        return
    target_user = context.args[0]
    monto_str = context.args[1].lower()
    target_id = obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text("❌ El usuario destino no está registrado en el bot.")
        return
    if target_id == user_id:
        await update.message.reply_text("🤡 No puedes darte dinero a ti mismo.")
        return
    if monto_str == "all":
        monto = info_origen["balance"]
    else:
        try:
            monto = int(monto_str)
        except ValueError:
            await update.message.reply_text("❌ Cantidad no válida.")
            return
    if monto <= 0 or info_origen["balance"] < monto:
        await update.message.reply_text("❌ Fondos insuficientes o cantidad inválida.")
        return
    actualizar_saldo(user_id, monto, es_ganancia=False)
    actualizar_saldo(target_id, monto, es_ganancia=True)
    await update.message.reply_text(f"💸 Le transferiste {m} {monto} a {target_user} con éxito.")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    obtener_o_crear_usuario(user_id, username)
    
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ultima_recarga FROM usuarios WHERE telegram_id = %s", (user_id,))
    
    fila = cursor.fetchone()
    ahora = datetime.datetime.now()
    
    # Validamos que la fila exista y que el valor de la columna no sea None
    if fila and fila[0] is not None:
        fecha_str = fila[0]
        ultima_fecha = datetime.datetime.fromisoformat(fecha_str)
        
        if (ahora - ultima_fecha).total_seconds() < 86400:
            tiempo_restante = 86400 - (ahora - ultima_fecha).total_seconds()
            horas = int(tiempo_restante // 3600)
            minutos = int((tiempo_restante % 3600) // 60)
            await update.message.reply_text(f"⏳ Ya reclamaste tu recompensa diaria. Vuelve en {horas}h y {minutos}m.")
            conn.close()
            return

    # Si llegó aquí es porque no ha reclamado o ya pasaron las 24 horas
    monedas_gratis = random.randint(50, 500) # Cambiado a mínimo 50 para que siempre sume algo
    cursor.execute("UPDATE usuarios SET balance = balance + %s, ultima_recarga = %s WHERE telegram_id = %s", 
                   (monedas_gratis, ahora.isoformat(), user_id))
    conn.commit()
    conn.close()
    
    m = obtener_moneda()
    await update.message.reply_text(f"🎁 ¡Bono Diario! Te tocaron {m} {monedas_gratis} aleatorias.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance FROM usuarios ORDER BY balance DESC LIMIT 10")
    filas = cursor.fetchall()
    conn.close()
    m = obtener_moneda()
    if not filas:
        await update.message.reply_text("La lista está vacía.")
        return
    texto_lead = "🏆 **LEADERBOARD - LOS MÁS RICOS** 🏆\n\n"
    for i, fila in enumerate(filas, start=1):
        medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
        prefijo = medallas.get(i, f"{i}.")
        texto_lead += f"{prefijo} @{fila[0]} — {m} {fila[1]}\n"
    await update.message.reply_markdown(texto_lead)

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url_api = "https://api.thecatapi.com/v1/images/search"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url_api)
            data = response.json()
            url_foto = data[0]["url"]
            await update.message.reply_photo(photo=url_foto, caption="🐱 ¡Gatito aleatorio listo, papu!")
        except Exception:
            await update.message.reply_text("❌ Error al obtener el gatito.")