import os
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Tus nuevos módulos
from comandos import ia, interaccion, general

# Instancia global
telegram_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    
    token = os.environ.get("TELEGRAM_TOKEN")
    telegram_app = Application.builder().token(token).build()

    # Tus nuevos Handlers
    telegram_app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("¡Hola! Soy Yulex.")))
    telegram_app.add_handler(CommandHandler("dado", general.dado))
    telegram_app.add_handler(CommandHandler("cat", general.cat))
    telegram_app.add_handler(CommandHandler("help", general.help_cmd))
    telegram_app.add_handler(CommandHandler("hug", interaccion.hug))
    telegram_app.add_handler(CommandHandler("kiss", interaccion.kiss))
    telegram_app.add_handler(CommandHandler("ship", interaccion.ship))
    telegram_app.add_handler(CommandHandler("8ball", general.ball8))
    
    # Dentro del bloque de handlers en bot.py
    telegram_app.add_handler(CommandHandler("slap", interaccion.slap))
    telegram_app.add_handler(CommandHandler("spank", interaccion.spank))
    telegram_app.add_handler(CommandHandler("kill", interaccion.kill))
    telegram_app.add_handler(CommandHandler("revive", interaccion.revive))
    
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ia.chat_con_ia))

    # Inicialización
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling(drop_pending_updates=True)
    
    print("🚀 Yulex está listo...")
    
    yield 
    
    # Apagado
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def index():
    return {"status": "Yulex_vivo"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000)) # Render asigna esta variable
    uvicorn.run(app, host="0.0.0.0", port=port)