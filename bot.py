import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# Importamos desde la carpeta comandos
from comandos import ia, interaccion, general

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()

    # Handlers usando la ruta de la carpeta
    app.add_handler(CommandHandler("dado", general.dado))
    app.add_handler(CommandHandler("gato", general.gato))
    app.add_handler(CommandHandler("help", general.help_cmd))
    app.add_handler(CommandHandler("abrazo", interaccion.abrazo))
    app.add_handler(CommandHandler("beso", interaccion.beso))
    app.add_handler(CommandHandler("ship", interaccion.ship))
    
    # Handler IA
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ia.chat_con_ia))

    print("🚀 Yulex está listo con su nueva estructura...")
    app.run_polling()

if __name__ == '__main__':
    main()