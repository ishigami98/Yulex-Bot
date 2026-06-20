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
    
    # Inicializar la base de datos
    inicializar_db()
    
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN")
        yield
        return

    # Construir la app de Telegram
    telegram_app = Application.builder().token(TOKEN).build()
    
    # 1. Borramos el webhook explícitamente primero
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)

    # === HANDLERS GENERALES ===
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("perfil", perfil))
    telegram_app.add_handler(CommandHandler("give_money", give_money)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("daily", daily))
    telegram_app.add_handler(CommandHandler("leaderboard", leaderboard)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("cat", cat))

    # === HANDLERS DE JUEGOS ===
    telegram_app.add_handler(CommandHandler("trabajar", trabajar))
    telegram_app.add_handler(CommandHandler("robar", robar))
    telegram_app.add_handler(CommandHandler("ruleta", ruleta))
    telegram_app.add_handler(CommandHandler("cock_fight", cock_fight)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("roll", roll))

    # === HANDLERS DE ADMINISTRACIÓN ===
    telegram_app.add_handler(CommandHandler("set_currency", set_currency)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("add_money", add_money)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("remove_money", remove_money)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("reset_economy", reset_economy)) # <-- Corregido
    telegram_app.add_handler(CommandHandler("reset_money", reset_money)) # <-- Corregido

    # 2. Inicializar y arrancar el bot de forma limpia sin argumentos obsoletos
    await telegram_app.initialize()
    await telegram_app.start()
    
    await telegram_app.updater.start_polling(
        drop_pending_updates=True,
        bootstrap_retries=3
    )
    print("🚀 El bot de Telegram está escuchando de forma segura desde la nube...")
    
    yield  # Aquí es donde FastAPI se mantiene corriendo en el puerto asignado
    
    # Código de apagado ordenado cuando Render detenga o reinicie el contenedor
    print("🛑 Apagando el bot de Telegram...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# Cambiamos el nombre de la variable a 'app' para que coincida perfectamente con Uvicorn
app = FastAPI(lifespan=lifespan)

@app.get("/")
def index():
    return {"status": "bot_vivo_y_camuflado"}

# 🚨 ESTO ES LO QUE LE DICE A RENDER QUE MANTENGA EL PROCESO VIVO
if __name__ == "__main__":
    # Render asigna el puerto dinámicamente en la variable de entorno PORT
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run("bot:app", host="0.0.0.0", port=puerto)