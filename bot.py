import os
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters # <-- Asegúrate de tener esta línea
from comandos import ia, interaccion, general

# El resto de tu código...

async def main(): # <--- Asegúrate que main sea async
    token = os.environ.get("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()

    # ... (Tus handlers se quedan igual) ...
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("¡Hola! Soy Yulex.")))
    # Handlers usando la ruta de la carpeta
    app.add_handler(CommandHandler("dado", general.dado))
    app.add_handler(CommandHandler("gato", general.gato))
    app.add_handler(CommandHandler("help", general.help_cmd))
    app.add_handler(CommandHandler("abrazo", interaccion.abrazo))
    app.add_handler(CommandHandler("beso", interaccion.beso))
    app.add_handler(CommandHandler("ship", interaccion.ship))
    
    # Handler IA
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ia.chat_con_ia))

    print("🚀 Yulex está listo...")
    # Usamos run_polling() de forma asíncrona
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Mantener el bot corriendo
    await asyncio.Event().wait()

if __name__ == '__main__':
    # Lanzamos el bucle asíncrono aquí
    asyncio.run(main())