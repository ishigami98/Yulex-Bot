import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

# Configuración de Logging estructurado (sin exponer datos confidenciales)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Extensiones y manejadores de python-telegram-bot v20+
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Inicialización de la base de datos
from database.conexion import inicializar_db

# Comandos modulares
from comandos.generales import start, help_command, perfil, daily, leaderboard, cat
from comandos.admin import (
    set_currency,
    add_money,
    remove_money,
    reset_economy,
    reset_money,
    give_money,
)
from comandos.juegos import (
    trabajar,
    crimen,
    robar,
    ruleta,
    cock_fight,
    roll,
    manejar_callback,
)
from comandos.afk import set_afk, check_afk

# Instancia global de la aplicación del bot
telegram_app = None


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador global de errores para la Application de python-telegram-bot."""
    logger.error(
        f"Excepción capturada procesando update {getattr(update, 'update_id', 'N/A')}: {context.error}",
        exc_info=context.error,
    )
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Ocurrió un error inesperado al procesar tu solicitud. Inténtalo más tarde."
            )
    except Exception as send_err:
        logger.error(f"No se pudo notificar el error al usuario: {send_err}")


def crear_aplicacion() -> Application:
    """
    Construye la instancia de Application (python-telegram-bot v20+)
    y registra todos los manejadores de comandos y eventos asíncronos.
    """
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("❌ ERROR CRÍTICO: No se encontró la variable de entorno TELEGRAM_TOKEN")

    app = Application.builder().token(token).build()

    # === MANEJADOR GLOBAL DE ERRORES ===
    app.add_error_handler(error_handler)

    # === COMANDOS GENERALES ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("cat", cat))

    # === JUEGOS Y ECONOMÍA ===
    app.add_handler(CommandHandler("trabajar", trabajar))
    app.add_handler(CommandHandler("crimen", crimen))
    app.add_handler(CommandHandler("robar", robar))  # Alias para compatibilidad con /robar
    app.add_handler(CommandHandler("ruleta", ruleta))
    app.add_handler(CommandHandler("cock_fight", cock_fight))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CallbackQueryHandler(manejar_callback))

    # === ADMINISTRACIÓN ===
    app.add_handler(CommandHandler("set_currency", set_currency))
    app.add_handler(CommandHandler("add_money", add_money))
    app.add_handler(CommandHandler("remove_money", remove_money))
    app.add_handler(CommandHandler("reset_economy", reset_economy))
    app.add_handler(CommandHandler("reset_money", reset_money))
    app.add_handler(CommandHandler("give_money", give_money))

    # === AFK Y TEXTO ===
    app.add_handler(CommandHandler("afk", set_afk))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_afk))

    return app


# Ciclo de vida asíncrono para FastAPI (compatible con despliegues web como Render)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app

    # 1. Inicializar base de datos
    inicializar_db()

    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN")
        yield
        return

    # 2. Inicializar Application de python-telegram-bot v20+
    telegram_app = crear_aplicacion()

    # 3. Arrancar polling en el bucle de eventos asíncrono
    try:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        print("🚀 El bot de Telegram está activo y escuchando en el bucle asíncrono...")
    except Exception as e:
        print(f"❌ Error arrancando el bot: {e}")
        yield
        return

    # Servidor activo
    yield

    # 4. Apagado ordenado en el bucle asíncrono
    print("🛑 Apagando el bot de Telegram...")
    try:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
    except Exception as e:
        print(f"Error en apagado del bot: {e}")


# Instancia de FastAPI para servicios web (health check / keep-alive)
app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"status": "ok", "bot": "Yulex Bot está en línea"}


def main():
    """
    Punto de entrada principal del bot:
    - En producción/Render (variable PORT definida): inicia Uvicorn con FastAPI y el bot en segundo plano.
    - En ejecución local directa: corre Application con bucle de eventos asíncrono nativo (run_polling).
    """
    inicializar_db()

    if os.environ.get("PORT"):
        puerto = int(os.environ.get("PORT", 8000))
        print(f"🌐 Detectado entorno con PORT={puerto}. Iniciando Uvicorn + FastAPI...")
        uvicorn.run("bot:app", host="0.0.0.0", port=puerto, reload=False)
    else:
        print("🚀 Iniciando bot con Application.run_polling() (bucle asíncrono)...")
        application = crear_aplicacion()
        application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
