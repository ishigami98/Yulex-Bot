import os
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Extensiones y manejadores de python-telegram-bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Importamos la inicialización del cliente de Supabase
from database.conexion import inicializar_db

# Importamos los comandos de tus módulos
from comandos.generales import start, help_command, perfil, daily, leaderboard, cat
from comandos.admin import set_currency, add_money, remove_money, reset_economy, reset_money, give_money
from comandos.juegos import trabajar, robar, ruleta, cock_fight, roll, manejar_callback

# Importamos las funciones del nuevo módulo AFK
from comandos.afk import set_afk, check_afk

# Instancia global de la aplicación del bot
telegram_app = None

# Ciclo de vida moderno para FastAPI (compatible con Render)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    
    # 1. Inicializar la base de datos (con cliente oficial)
    inicializar_db()
    
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN")
        yield
        return

    # 2. Construir la app de Telegram
    telegram_app = Application.builder().token(TOKEN).build()
    
    # Borramos el webhook para evitar conflictos previos y limpiar actualizaciones colgadas
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)

    # === REGISTRO DE HANDLERS ===
    
    # Generales
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("perfil", perfil))
    telegram_app.add_handler(CommandHandler("give_money", give_money))
    telegram_app.add_handler(CommandHandler("daily", daily))
    telegram_app.add_handler(CommandHandler("leaderboard", leaderboard))
    telegram_app.add_handler(CommandHandler("cat", cat))
    
    # Juegos
    telegram_app.add_handler(CommandHandler("trabajar", trabajar))
    telegram_app.add_handler(CommandHandler("robar", robar))
    telegram_app.add_handler(CommandHandler("ruleta", ruleta))
    telegram_app.add_handler(CommandHandler("cock_fight", cock_fight))
    telegram_app.add_handler(CommandHandler("roll", roll))
    telegram_app.add_handler(CallbackQueryHandler(manejar_callback))
    
    # Admin
    telegram_app.add_handler(CommandHandler("set_currency", set_currency))
    telegram_app.add_handler(CommandHandler("add_money", add_money))
    telegram_app.add_handler(CommandHandler("remove_money", remove_money))
    telegram_app.add_handler(CommandHandler("reset_economy", reset_economy))
    telegram_app.add_handler(CommandHandler("reset_money", reset_money))
    
    # AFK (Comando Slash)
    telegram_app.add_handler(CommandHandler("afk", set_afk))
    
    # === Filtro de Texto Global (AFK y triggers de texto plano) ===
    # IMPORTANTE: Va al final para que no intercepte ni bloquee los comandos anteriores.
    # filters.TEXT & ~filters.COMMAND procesa solo mensajes normales que no sean /comandos.
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_afk))

    # 3. Arrancar polling de forma limpia
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling(drop_pending_updates=True)
    
    print("🚀 El bot de Telegram está activo y escuchando...")
    
    yield 
    
    # Apagado ordenado del proceso al detener el servicio
    print("🛑 Apagando el bot...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# Instancia de FastAPI con el ciclo de vida configurado
app = FastAPI(lifespan=lifespan)

# Ruta básica de Health Check para que Render sepa que el servidor web sigue vivo
@app.get("/")
def read_root():
    return {"status": "ok", "bot": "Yulex Bot está en línea"}

if __name__ == "__main__":
    # El servidor web corre en el puerto provisto por Render (o 8000 localmente)
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run("bot:app", host="0.0.0.0", port=puerto, reload=False)
