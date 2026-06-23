import os
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from comandos import ia, interaccion, general

async def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("¡Hola! Soy Yulex.")))
    app.add_handler(CommandHandler("dado", general.dado))
    app.add_handler(CommandHandler("gato", general.gato))
    app.add_handler(CommandHandler("help", general.help_cmd))
    app.add_handler(CommandHandler("abrazo", interaccion.abrazo))
    app.add_handler(CommandHandler("beso", interaccion.beso))
    app.add_handler(CommandHandler("ship", interaccion.ship))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ia.chat_con_ia))

    print("🚀 Yulex está listo...")
    
    # Inicialización asíncrona
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Mantiene el bot vivo
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())