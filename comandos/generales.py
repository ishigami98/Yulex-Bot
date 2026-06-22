import datetime
import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes
# Importamos supabase directamente desde la conexión
from database.conexion import (
    obtener_o_crear_usuario, obtener_moneda, supabase
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Esta función debería ser async y usar await, asegúrate de actualizarla en conexion.py
    info = await obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    
    if info.get("nuevo"):
        await update.message.reply_text(f"👋 ¡Hola {username}! ¡Bienvenido al CasinoBot!\nTe he regalado {m} 500 de bienvenida. ¡Usa /help para ver los comandos!")
    else:
        await update.message.reply_text(f"¡Hola de nuevo, {username}! Tu saldo actual es de {m} {info['balance']}.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = obtener_moneda()
    texto_help = (
        "🤖 **Lista de Comandos Disponibles** 🤖\n\n"
        "**⚙️ Admin / Moderación:**\n"
        "🔸 `/set_currency` - Cambia el símbolo global.\n"
        "🔸 `/add_money` - Añade dinero.\n\n"
        "💸 **Economía:** /perfil, /daily, /leaderboard\n"
        "🎲 **Juegos:** /trabajar, /robar, /ruleta, /cock_fight, /roll, /cat"
    )
    await update.message.reply_text(texto_help, parse_mode="Markdown")

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Uso correcto de await con el cliente de Supabase
    res = await supabase.table("usuarios").select("*").eq("telegram_id", user_id).execute()
    
    if not res.data:
        await update.message.reply_text("❌ No tienes un perfil creado. Usa /start")
        return
        
    u = res.data[0]
    m = obtener_moneda()
    texto = (f"👤 **Perfil de @{u['username']}**\n\n"
             f"{m} Saldo: {u['balance']}\n"
             f"📈 Victorias: {u.get('ganadas', 0)}\n"
             f"📉 Derrotas: {u.get('perdidas', 0)}")
    await update.message.reply_markdown(texto)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    res = await supabase.table("usuarios").select("ultima_daily, balance").eq("telegram_id", user_id).execute()
    
    if not res.data:
        await update.message.reply_text("❌ Primero crea tu perfil con /start")
        return

    ultima_daily = res.data[0].get("ultima_daily")
    ahora = datetime.datetime.now()
    
    if ultima_daily:
        fecha_ultima = datetime.datetime.fromisoformat(ultima_daily)
        if (ahora - fecha_ultima).days < 1:
            await update.message.reply_text("⏳ Ya reclamaste tu bono hoy. Vuelve mañana.")
            return

    recompensa = random.randint(100, 300)
    nuevo_balance = res.data[0]["balance"] + recompensa
    
    await supabase.table("usuarios").update({
        "balance": nuevo_balance,
        "ultima_daily": ahora.isoformat()
    }).eq("telegram_id", user_id).execute()
    
    await update.message.reply_text(f"🎁 ¡Bono Diario! Ganaste {obtener_moneda()} {recompensa}.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = await supabase.table("usuarios").select("username, balance").order("balance", desc=True).limit(10).execute()
    
    if not res.data:
        await update.message.reply_text("La lista está vacía.")
        return
        
    m = obtener_moneda()
    texto_lead = "🏆 **TOP 10 RICOS** 🏆\n\n"
    for i, u in enumerate(res.data, start=1):
        texto_lead += f"{i}. @{u['username']} — {m} {u['balance']}\n"
    await update.message.reply_markdown(texto_lead)

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.thecatapi.com/v1/images/search")
        data = r.json()
        await update.message.reply_photo(data[0]["url"], caption="Toma un gatito 🐱")

