import os
import asyncio
from telegram.ext import Application, CommandHandler
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Importamos todo desde tus carpetas modulares
from database.conexion import inicializar_db
from comandos.generales import start, help_command, perfil, give_money, daily, leaderboard, cat
from comandos.juegos import trabajar, robar, ruleta, cock_fight, roll
from comandos.admin import set_currency, add_money, remove_money, reset_economy, reset_money

# Creamos una instancia global de la aplicación del bot
telegram_app = None

# 🕒 El manejador de ciclo de vida moderno de FastAPI (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    print("🔗 Conexión exitosa e inicializada con Supabase por HTTP!")
    
    # Inicializar la base de datos
    inicializar_db()
    
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN")
        yield
        return

    # Construir la app de Telegram
    telegram_app = Application.builder().token(TOKEN).build()
    
    # 1. Borramos webhook explícitamente primero
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)

    # === [Aquí van todos tus telegram_app.add_handler(...) tal cual los tienes] ===

    # 2. Inicializamos forzando limpieza de conexiones colgadas
    await telegram_app.initialize()
    await telegram_app.start()
    
    # 3. Al iniciar el polling, le decimos a Telegram: "Yo soy el único dueño del bot ahora"
    await telegram_app.updater.start_polling(
        drop_pending_updates=True, 
        bootstrap_retries=3,
        clean=True # Esto barre cualquier cola vieja que cause el Conflict
    )
    print("🚀 El bot de Telegram está escuchando de forma segura desde la nube...")

    # === HANDLERS GENERALES ===
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("perfil", perfil))
    telegram_app.add_handler(CommandHandler("give", give_money))
    telegram_app.add_handler(CommandHandler("daily", daily))
    telegram_app.add_handler(CommandHandler("top", leaderboard))
    telegram_app.add_handler(CommandHandler("cat", cat))

    # === HANDLERS DE JUEGOS ===
    telegram_app.add_handler(CommandHandler("trabajar", trabajar))
    telegram_app.add_handler(CommandHandler("robar", robar))
    telegram_app.add_handler(CommandHandler("ruleta", ruleta))
    telegram_app.add_handler(CommandHandler("pollo", cock_fight))
    telegram_app.add_handler(CommandHandler("roll", roll))

    # === HANDLERS DE ADMINISTRACIÓN ===
    telegram_app.add_handler(CommandHandler("setcurrency", set_currency))
    telegram_app.add_handler(CommandHandler("addmoney", add_money))
    telegram_app.add_handler(CommandHandler("removemoney", remove_money))
    telegram_app.add_handler(CommandHandler("reseteconomy", reset_economy))
    telegram_app.add_handler(CommandHandler("resetmoney", reset_money))

    # Inicializar y arrancar el bot de forma nativa
    await telegram_app.initialize()
    await telegram_app.start()
    
    # Quitamos 'clean' para que no rompa por tipo de argumento
    await telegram_app.updater.start_polling(
        drop_pending_updates=True, 
        bootstrap_retries=3
    )
    print("🚀 El bot de Telegram está escuchando de forma segura desde la nube...")
    
    yield  # Aquí es donde FastAPI se queda corriendo feliz
    
    # Código de apagado cuando Render detenga el servicio
    print("🛑 Apagando el bot de Telegram...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# La mini app web usando el ciclo moderno lifespan
app_web = FastAPI(lifespan=lifespan)

@app_web.get("/")
def index():
    return {"status": "bot_vivo_y_camuflado"}

# 🚨 ESTO ES LO QUE LE DICE A RENDER QUE MANTENGA EL PROCESO VIVO
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 10000))
    uvicorn.run("bot:app_web", host="0.0.0.0", port=puerto, log_level="info")