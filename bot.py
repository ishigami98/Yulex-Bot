import psycopg2  
import random
import datetime
import httpx
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from fastapi import FastAPI
import uvicorn

# === 🛠️ CONFIGURACIÓN HTTP DE SUPABASE ===
SUPABASE_URL = "https://nkufkghwwbrlesdwbano.supabase.co"

# Usamos os.environ para jalar las variables de Render de forma segura
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_secret_8BS1aZGvhxQJ1Q0sO0C_Lg_oSHmMgxA")
CREADOR_ID = int(os.environ.get("CREADOR_ID", 5235708855))

# Instancia de FastAPI para simular una Web de cara a Render (Capa Gratis)
app_web = FastAPI()

@app_web.get("/")
def read_root():
    return {"status": "bot_vivo_y_camuflado"}

class FalsaConexion:
    def __init__(self):
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    def cursor(self):
        return FalsoCursor(self.headers)
    def commit(self):
        pass
    def close(self):
        pass

class FalsoCursor:
    def __init__(self, headers):
        self.headers = headers
        self.resultados = None
        self.index = 0

    def execute(self, query, params=None):
        if params:
            formated_params = tuple(f"'{p}'" if isinstance(p, str) else str(p) for p in params)
            query = query % formated_params
            
        query_limpia = " ".join(query.split())
        url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
        payload = {"query": query_limpia}
        
        try:
            response = httpx.post(url, json=payload, headers=self.headers, timeout=15.0)
            if response.status_code in [200, 201]:
                self.resultados = response.json()
            else:
                self.resultados = []
        except Exception:
            self.resultados = []
        self.index = 0

    def fetchone(self):
        if self.resultados and self.index < len(self.resultados):
            res = self.resultados[self.index]
            self.index += 1
            return tuple(res.values()) if isinstance(res, dict) else res
        return None

    def fetchall(self):
        if self.resultados:
            return [tuple(res.values()) if isinstance(res, dict) else res for res in self.resultados]
        return []

    def close(self):
        pass

def conectar_db():
    return FalsaConexion()

def inicializar_db():
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 500,
                ganadas INTEGER DEFAULT 0,
                perdidas INTEGER DEFAULT 0,
                ultima_recarga TEXT,
                pollos_ganados INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('moneda', '🪙') ON CONFLICT (clave) DO NOTHING")
        conn.commit()
        conn.close()
        print("🔗 Conexión exitosa e inicializada con Supabase por HTTP!")
    except Exception as e:
        print(f"❌ Error al conectar o inicializar Supabase: {e}")

def obtener_moneda():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = 'moneda'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "🪙"

def obtener_o_crear_usuario(telegram_id, username):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, ganadas, perdidas, pollos_ganados FROM usuarios WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    username_limpio = username.replace("@", "").lower() if username else f"user_{telegram_id}"
    
    if not user:
        cursor.execute(
            "INSERT INTO usuarios (telegram_id, username, balance, ganadas, perdidas, pollos_ganados) VALUES (%s, %s, 500, 0, 0, 0)",
            (telegram_id, username_limpio)
        )
        conn.commit()
        conn.close()
        return {"balance": 500, "ganadas": 0, "perdidas": 0, "pollos": 0, "nuevo": True}
    
    cursor.execute("UPDATE usuarios SET username = %s WHERE telegram_id = %s", (username_limpio, telegram_id))
    conn.commit()
    conn.close()
    return {"balance": user[0], "ganadas": user[1], "perdidas": user[2], "pollos": user[3], "nuevo": False}

def obtener_id_por_username(username):
    conn = conectar_db()
    cursor = conn.cursor()
    username_limpio = username.replace("@", "").lower().strip()
    cursor.execute("SELECT telegram_id FROM usuarios WHERE username = %s", (username_limpio,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    conn = conectar_db()
    cursor = conn.cursor()
    if es_ganancia:
        cursor.execute("""
            UPDATE usuarios 
            SET balance = balance + %s, ganadas = ganadas + %s 
            WHERE telegram_id = %s
        """, (cantidad, cantidad, telegram_id))
    else:
        cursor.execute("""
            UPDATE usuarios 
            SET balance = balance - %s, perdidas = perdidas + %s 
            WHERE telegram_id = %s
        """, (cantidad, cantidad, telegram_id))
    conn.commit()
    conn.close()

async def es_administrador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == CREADOR_ID:
        return True
    if update.effective_chat.type in ["group", "supergroup"]:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            return True
    return False

# === COMANDOS ===
async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos de administrador.")
        return
    if not context.args:
        await update.message.reply_text("❌ Uso: `/set_currency <símbolo>`")
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
        await update.message.reply_text("❌ Uso: `/add_money @usuario <cantidad>`")
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
    actualizar_saldo(target_id, cantidad, es_ganancia=True)
    m = obtener_moneda()
    await update.message.reply_text(f"✅ Se añadieron {m} {cantidad} al saldo de {target_user}.")

async def remove_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No eres administrador.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/remove_money @usuario <cantidad>`")
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
    await update.message.reply_text("🚨 **LA ECONOMÍA HA SIDO REINICIADA**.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    info = obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    if info["nuevo"]:
        await update.message.reply_text(f"👋 ¡Hola {username}! Bienvenido.\nTe regalé {m} 500 de bienvenida. ¡Usa /help!")
    else:
        await update.message.reply_text(f"¡Hola {username}! Saldo actual: {m} {info['balance']}.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = obtener_moneda()
    texto_help = (
        "🤖 **Lista de Comandos Disponibles** 🤖\n\n"
        "🔸 `/start` - Inicia el bot.\n"
        "🔸 `/help` - Muestra esta lista.\n"
        "🔸 `/perfil` - Mira tus estadísticas.\n"
        "🔸 `/daily` - Monedas gratis cada 24h.\n"
        "🔸 `/give_money <@usuario> <cant>` - Regala dinero.\n"
        "🔸 `/leaderboard` - Ranking.\n"
        "🔸 `/trabajar` - Consigue empleo.\n"
        "🔸 `/robar` - Atraco aleatorio.\n"
        "🔸 `/ruleta <cantidad> <rojo/negro>` - Apuesta.\n"
        "🔸 `/cock_fight <apuesta>` - Pelea de pollos.\n"
        "🔸 `/roll` - Tira un dado.\n"
        "🔸 `/cat` - Foto de gato."
    )
    await update.message.reply_markdown(texto_help)

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    info = obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    texto_perfil = f"👤 **PERFIL** 👤\n\n🔹 @{username}\n🔹 Saldo: {m} {info['balance']}\n📈 Ganadas: {info['ganadas']}\n📉 Perdidas: {info['perdidas']}\n🐓 Pollos: {info['pollos']}"
    await update.message.reply_markdown(texto_perfil)

async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info_origen = obtener_o_crear_usuario(user_id, update.effective_user.username)
    m = obtener_moneda()
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/give_money @usuario <cantidad>`")
        return
    target_user = context.args[0]
    monto_str = context.args[1].lower()
    target_id = obtener_id_por_username(target_user)
    if not target_id or target_id == user_id:
        await update.message.reply_text("❌ Usuario inválido.")
        return
    monto = info_origen["balance"] if monto_str == "all" else int(monto_str)
    if monto <= 0 or info_origen["balance"] < monto:
        await update.message.reply_text("❌ Fondos insuficientes.")
        return
    actualizar_saldo(user_id, monto, es_ganancia=False)
    actualizar_saldo(target_id, monto, es_ganancia=True)
    await update.message.reply_text(f"💸 Transferiste {m} {monto} a {target_user}.")

async def reset_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET balance = 500 WHERE telegram_id = %s", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("🔄 Saldo reseteado a 500.")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ultima_recarga FROM usuarios WHERE telegram_id = %s", (user_id,))
    fecha_str = cursor.fetchone()[0]
    ahora = datetime.datetime.now()
    if fecha_str and (ahora - datetime.datetime.fromisoformat(fecha_str)).total_seconds() < 86400:
        await update.message.reply_text("⏳ Vuelve mañana.")
        conn.close()
        return
    monedas = random.randint(50, 500)
    cursor.execute("UPDATE usuarios SET balance = balance + %s, ultima_recarga = %s WHERE telegram_id = %s", (monedas, ahora.isoformat(), user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🎁 ¡Bono Diario! Ganaste {monedas}.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance FROM usuarios ORDER BY balance DESC LIMIT 10")
    filas = cursor.fetchall()
    conn.close()
    m = obtener_moneda()
    texto_lead = "🏆 **TOP RICOS** 🏆\n\n"
    for i, fila in enumerate(filas, start=1):
        texto_lead += f"{i}. @{fila[0]} — {m} {fila[1]}\n"
    await update.message.reply_markdown(texto_lead)

async def trabajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    m = obtener_moneda()
    paga = random.randint(100, 400)
    actualizar_saldo(user_id, paga, es_ganancia=True)
    await update.message.reply_text(f"💼 Trabajaste duro y ganaste {m} {paga}.")

async def robar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    m = obtener_moneda()
    resultado = random.randint(-200, 400)
    if resultado >= 0:
        actualizar_saldo(user_id, resultado, es_ganancia=True)
        await update.message.reply_text(f"🥷 Robaste {m} {resultado} con éxito.")
    else:
        actualizar_saldo(user_id, abs(resultado), es_ganancia=False)
        await update.message.reply_text(f"🚓 Te multaron con {m} {abs(resultado)}.")

async def ruleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = obtener_o_crear_usuario(user_id, update.effective_user.username)
    if len(context.args) < 2: return
    monto = info["balance"] if context.args[0] == "all" else int(context.args[0])
    color = context.args[1].lower()
    if color not in ["rojo", "negro"] or monto <= 0 or monto > info["balance"]: return
    res = random.choice(["rojo", "negro"])
    if color == res:
        actualizar_saldo(user_id, monto, es_ganancia=True)
        await update.message.reply_text(f"🎰 Cayó {res}! ¡Ganaste {monto}!")
    else:
        actualizar_saldo(user_id, monto, es_ganancia=False)
        await update.message.reply_text(f"🎰 Cayó {res}... Perdiste {monto}.")

async def cock_fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = obtener_o_crear_usuario(user_id, update.effective_user.username)
    if not context.args: return
    apuesta = int(context.args[0])
    if apuesta <= 0 or info["balance"] < apuesta: return
    win = random.randint(1, 100) <= 55
    if win:
        actualizar_saldo(user_id, apuesta, es_ganancia=True)
        await update.message.reply_text(f"🏆 ¡Tu gallo ganó! +{apuesta}")
    else:
        actualizar_saldo(user_id, apuesta, es_ganancia=False)
        await update.message.reply_text(f"💀 Tu gallo perdió. -{apuesta}")

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = random.randint(1, 6)
    await update.message.reply_text(f"🎲 Dado: **{res}**")

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url_api = "https://api.thecatapi.com/v1/images/search"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url_api)
            url_foto = response.json()[0]["url"]
            await update.message.reply_photo(photo=url_foto, caption="🐱 ¡Gatito!")
        except Exception:
            await update.message.reply_text("❌ Error al obtener gato.")

# === ASYNC RUNNER PARA RENDER (Engaño de Servidor Web) ===
async def iniciar_bot():
    inicializar_db()
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR: Falta TELEGRAM_TOKEN")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("set_currency", set_currency))
    app.add_handler(CommandHandler("add_money", add_money))
    app.add_handler(CommandHandler("remove_money", remove_money))
    app.add_handler(CommandHandler("reset_economy", reset_economy))
    app.add_handler(CommandHandler("give_money", give_money))
    app.add_handler(CommandHandler("reset_money", reset_money))
    app.add_handler(CommandHandler("trabajar", trabajar))
    app.add_handler(CommandHandler("robar", robar))
    app.add_handler(CommandHandler("ruleta", ruleta))
    app.add_handler(CommandHandler("cock_fight", cock_fight))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("cat", cat))
    
    print("🚀 Bot de Telegram escuchando de forma segura...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

@app_web.on_event("startup")
def on_startup():
    asyncio.create_task(iniciar_bot())

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app_web, host="0.0.0.0", port=puerto)