import datetime
import random
import httpx
from telegram import Update
from telegram.ext import ContextTypes
<<<<<<< HEAD
# Importamos supabase directamente desde la conexión
from database.conexion import (
    obtener_o_crear_usuario, obtener_moneda, supabase
)
=======
from database.conexion import obtener_o_crear_usuario, obtener_moneda, supabase
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
<<<<<<< HEAD
    # Esta función debería ser async y usar await, asegúrate de actualizarla en conexion.py
=======
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91
    info = await obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    
    if info.get("nuevo"):
        await update.message.reply_text(f"👋 ¡Hola {username}! ¡Bienvenido al CasinoBot!\nTe he regalado {m} 500 de bienvenida. ¡Usa /help para ver los comandos!")
    else:
        await update.message.reply_text(f"¡Hola de nuevo, {username}! Tu saldo actual es de {m} {info['balance']}.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = obtener_moneda()
    texto_help = (
<<<<<<< HEAD
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
=======
        "🤖 <b>Lista de Comandos Disponibles</b> 🤖\n\n"
        "<b>⚙️ Admin / Moderación:</b>\n"
        "🔸 <code>/set_currency</code> - Cambia el símbolo global.\n"
        "🔸 <code>/add_money</code> - Añade dinero.\n\n"
        "💸 <b>Economía:</b> /perfil, /daily, /leaderboard\n"
        "🎲 <b>Juegos:</b> /trabajar, /robar, /ruleta, /cock_fight, /roll, /cat"
    )
    await update.message.reply_text(texto_help, parse_mode="HTML")

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # CORRECCIÓN: Quitamos 'await'
    res = supabase.table("usuarios").select("*").eq("telegram_id", user_id).execute()
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91
    
    if not res.data:
        await update.message.reply_text("❌ No tienes un perfil creado. Usa /start")
        return
        
    u = res.data[0]
    m = obtener_moneda()
<<<<<<< HEAD
    texto = (f"👤 **Perfil de @{u['username']}**\n\n"
             f"{m} Saldo: {u['balance']}\n"
             f"📈 Victorias: {u.get('ganadas', 0)}\n"
             f"📉 Derrotas: {u.get('perdidas', 0)}")
    await update.message.reply_markdown(texto)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    res = await supabase.table("usuarios").select("ultima_daily, balance").eq("telegram_id", user_id).execute()
=======
    
    texto = (f"👤 <b>Perfil de @{u['username']}</b>\n\n"
             f"{m} Saldo: {u['balance']}\n"
             f"📈 Victorias: {u.get('ganadas', 0)}\n"
             f"📉 Derrotas: {u.get('perdidas', 0)}")
    await update.message.reply_text(texto, parse_mode="HTML")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # CORRECCIÓN: Quitamos 'await'
    res = supabase.table("usuarios").select("ultima_daily, balance").eq("telegram_id", user_id).execute()
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91
    
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
    
<<<<<<< HEAD
    await supabase.table("usuarios").update({
=======
    # CORRECCIÓN: Quitamos 'await'
    supabase.table("usuarios").update({
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91
        "balance": nuevo_balance,
        "ultima_daily": ahora.isoformat()
    }).eq("telegram_id", user_id).execute()
    
    await update.message.reply_text(f"🎁 ¡Bono Diario! Ganaste {obtener_moneda()} {recompensa}.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
<<<<<<< HEAD
    res = await supabase.table("usuarios").select("username, balance").order("balance", desc=True).limit(10).execute()
=======
    # CORRECCIÓN: Quitamos 'await'
    res = supabase.table("usuarios").select("username, balance").order("balance", desc=True).limit(10).execute()
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91
    
    if not res.data:
        await update.message.reply_text("La lista está vacía.")
        return
        
    m = obtener_moneda()
<<<<<<< HEAD
    texto_lead = "🏆 **TOP 10 RICOS** 🏆\n\n"
    for i, u in enumerate(res.data, start=1):
        texto_lead += f"{i}. @{u['username']} — {m} {u['balance']}\n"
    await update.message.reply_markdown(texto_lead)
=======
    texto_lead = "🏆 <b>TOP 10 RICOS</b> 🏆\n\n"
    for i, u in enumerate(res.data, start=1):
        texto_lead += f"{i}. @{u['username']} — {m} {u['balance']}\n"
        
    await update.message.reply_text(texto_lead, parse_mode="HTML")
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.thecatapi.com/v1/images/search")
        data = r.json()
<<<<<<< HEAD
        await update.message.reply_photo(data[0]["url"], caption="Toma un gatito 🐱")

=======
        await update.message.reply_photo(data[0]["url"], caption="Toma un gatito 🐱")
>>>>>>> c29d3a96c4cae04ab1577530073bc15aad2b4a91
