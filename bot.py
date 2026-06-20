import os
import asyncio
from telegram.ext import Application, CommandHandler
from fastapi import FastAPI
import uvicorn

# Importaciones de tus módulos modulares
from database.conexion import inicializar_db
from comandos.generales import start, help_command, perfil, give_money, daily, leaderboard, cat
from comandos.juegos import trabajar, robar, ruleta, cock_fight, roll
from comandos.admin import set_currency, add_money, remove_money, reset_economy, reset_money

# Creamos una mini app web para engañar a Render
app_web = FastAPI()

@app_web.get("/")
def read_root():
    return {"status": "bot_vivo_y_camuflado"}

async def iniciar_bot():
    inicializar_db()
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    
    # Registro de todos tus comandos (se quedan igual)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("give_money", give_money))
    app.add_handler(CommandHandler("cat", cat))
    app.add_handler(CommandHandler("trabajar", trabajar))
    app.add_handler(CommandHandler("robar", robar))
    app.add_handler(CommandHandler("ruleta", ruleta))
    app.add_handler(CommandHandler("cock_fight", cock_fight))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("set_currency", set_currency))
    app.add_handler(CommandHandler("add_money", add_money))
    app.add_handler(CommandHandler("remove_money", remove_money))
    app.add_handler(CommandHandler("reset_economy", reset_economy))
    app.add_handler(CommandHandler("reset_money", reset_money))
    
    print("🚀 El bot de Telegram está escuchando de forma segura...")
    
    # Arrancamos el bot de Telegram en segundo plano de forma asíncrona
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

@app_web.on_event("startup")
def on_startup():
    # Cuando la web enciende, dispara el bot de Telegram
    asyncio.create_task(iniciar_bot())

if __name__ == "__main__":
    # Render nos da un puerto dinámico en la variable PORT, si no usa el 8000
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app_web, host="0.0.0.0", port=puerto)