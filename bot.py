import os
import asyncio
from telegram.ext import Application, CommandHandler
from fastapi import FastAPI
import uvicorn

# Importamos todo desde tus carpetas modulares
from database.conexion import inicializar_db
from comandos.generales import start, help_command, perfil, give_money, daily, leaderboard, cat
from comandos.juegos import trabajar, robar, ruleta, cock_fight, roll
from comandos.admin import set_currency, add_money, remove_money, reset_economy, reset_money

# La mini app web para camuflarnos en la capa gratis de Render
app_web = FastAPI()

@app_web.get("/")
def read_root():
    return {"status": "bot_vivo_y_camuflado"}

async def iniciar_bot():
    # Inicializa las tablas en Supabase
    inicializar_db()
    
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    
    # 🚨 EL TRUCO ANTI-CONFLICTO: Limpia cualquier webhook o sesión colgada antes de arrancar
    await app.bot.delete_webhook(drop_pending_updates=True)
    
    # Registro de Comandos Generales (Vienen de comandos/generales.py)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("give_money", give_money))
    app.add_handler(CommandHandler("cat", cat))
    
    # Registro de Comandos de Juegos (Vienen de comandos/juegos.py)
    app.add_handler(CommandHandler("trabajar", trabajar))
    app.add_handler(CommandHandler("robar", robar))
    app.add_handler(CommandHandler("ruleta", ruleta))
    app.add_handler(CommandHandler("cock_fight", cock_fight))
    app.add_handler(CommandHandler("roll", roll))
    
    # Registro de Comandos Administrativos (Vienen de comandos/admin.py)
    app.add_handler(CommandHandler("set_currency", set_currency))
    app.add_handler(CommandHandler("add_money", add_money))
    app.add_handler(CommandHandler("remove_money", remove_money))
    app.add_handler(CommandHandler("reset_economy", reset_economy))
    app.add_handler(CommandHandler("reset_money", reset_money))
    
    print("🚀 El bot de Telegram está escuchando de forma segura desde la nube...")
    
    # Arrancamos el bot en segundo plano de forma asíncrona compartiendo hilos con FastAPI
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

@app_web.on_event("startup")
def on_startup():
    # Al encender la web, dispara el hilo del bot de Telegram en paralelo
    asyncio.create_task(iniciar_bot())

if __name__ == "__main__":
    # Render nos exige escuchar en el puerto que ellos digan mediante la variable PORT
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app_web, host="0.0.0.0", port=puerto)