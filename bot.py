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
def index():
    return {"status": "bot_vivo_y_camuflado"}

# 🚨 CAMBIAMOS LA FUNCIÓN DE INICIO PARA QUE TRABAJE EN SEGUNDO PLANO
async def correr_polling_en_fondo():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN")
        return

    # Inicializar la base de datos antes
    inicializar_db()

    app = Application.builder().token(TOKEN).build()
    
    # Forzar la limpieza de webhooks viejos
    await app.bot.delete_webhook(drop_pending_updates=True)

    # === HANDLERS GENERALES ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("give", give_money))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("top", leaderboard))
    app.add_handler(CommandHandler("cat", cat))

    # === HANDLERS DE JUEGOS ===
    app.add_handler(CommandHandler("trabajar", trabajar))
    app.add_handler(CommandHandler("robar", robar))
    app.add_handler(CommandHandler("ruleta", ruleta))
    app.add_handler(CommandHandler("pollo", cock_fight))
    app.add_handler(CommandHandler("roll", roll))

    # === HANDLERS DE ADMINISTRACIÓN ===
    app.add_handler(CommandHandler("setcurrency", set_currency))
    app.add_handler(CommandHandler("addmoney", add_money))
    app.add_handler(CommandHandler("removemoney", remove_money))
    app.add_handler(CommandHandler("reseteconomy", reset_economy))
    app.add_handler(CommandHandler("resetmoney", reset_money))

    print("🚀 El bot de Telegram está escuchando de forma segura desde la nube...")
    
    # Inicializa el bot de manera asíncrona sin bloquear a FastAPI
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    print("🚀 El bot de Telegram está escuchando de forma segura desde la nube...")
    
    # Inicializa el bot de manera asíncrona sin bloquear a FastAPI
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # 🚨 MANTENER AL BOT DESPIERTO EN SEGUNDO PLANO INFINITAMENTE
    while True:
        await asyncio.sleep(3600)  # Duerme una hora y repite el ciclo para no gastar CPU
# 🕒 Evento de inicio de FastAPI corregido
@app_web.on_event("startup")
async def startup_event():
    print("🔗 Conexión exitosa e inicializada con Supabase por HTTP!")
    # Esto lanza el bot en paralelo sin congelar el servidor web
    asyncio.create_task(correr_polling_en_fondo())