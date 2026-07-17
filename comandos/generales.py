import datetime
import random
import httpx
import logging  # Importante para logs internos
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import obtener_o_crear_usuario, obtener_moneda, actualizar_saldo

# Configurar logs para que veamos los errores en la consola sin mostrarlos al usuario
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    info = await obtener_o_crear_usuario(user_id, username)
    m = obtener_moneda()
    
    if info.get("nuevo"):
        await update.message.reply_text(
            f"👋 ¡Hola {username}! ¡Bienvenido al CasinoBot!\n"
            f"Te he regalado 500 {m} de bienvenida. ¡Usa /help para ver los comandos!"
        )
    else:
        # Usamos .get('balance', 0) para evitar KeyError
        saldo = info.get('balance', 0)
        await update.message.reply_text(f"¡Hola de nuevo, {username}! Tu saldo actual es de {saldo} {m}.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = obtener_moneda()
    texto_help = (
        "🤖 <b>Lista de Comandos Disponibles</b> 🤖\n\n"
        "<b>⚙️ Admin / Moderación:</b>\n"
        "🔸 <code>/set_currency</code> - Cambia el símbolo global.\n"
        "🔸 <code>/add_money</code> - Añade dinero.\n\n"
        "💸 <b>Economía:</b> /perfil, /daily, /leaderboard\n"
        "🎲 <b>Juegos:</b> /trabajar, /robar, /ruleta, /cock_fight, /roll, /cat"
    )
    await update.message.reply_text(texto_help, parse_mode="HTML")

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        # Usamos la función de conexión, no supabase directo
        info = await obtener_o_crear_usuario(user_id, update.effective_user.username)
        m = obtener_moneda()
        
        texto = (f"👤 <b>Perfil de @{info.get('username', 'usuario')}</b>\n\n"
                 f"Saldo: {info.get('balance', 0)} {m}\n"
                 f"📈 Victorias: {info.get('ganadas', 0)}\n"
                 f"📉 Derrotas: {info.get('perdidas', 0)}")
        await update.message.reply_text(texto, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error en perfil: {e}")
        await update.message.reply_text("❌ Hubo un error al cargar tu perfil. Inténtalo más tarde.")

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.thecatapi.com/v1/images/search")
            data = r.json()
            # Validamos que la API nos devuelva datos antes de acceder
            if data and isinstance(data, list) and len(data) > 0:
                await update.message.reply_photo(data[0]["url"], caption="Toma un gatito 🐱")
            else:
                await update.message.reply_text("❌ No pude encontrar un gatito, intenta de nuevo.")
    except Exception as e:
        logger.error(f"Error en cat: {e}")
        await update.message.reply_text("❌ Error al buscar el gatito.")