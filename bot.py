import os
from telegram.ext import Application, CommandHandler

# Importaciones de nuestros módulos modulares
from database.conexion import inicializar_db
from comandos.generales import start, help_command, perfil, give_money, daily, leaderboard, cat
from comandos.juegos import trabajar, robar, ruleta, cock_fight, roll
from comandos.admin import set_currency, add_money, remove_money, reset_economy, reset_money

def main():
    # Inicialización del sistema
    inicializar_db()
    
    # Token dinámico desde variables de entorno
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN en el sistema.")
        return

    app = Application.builder().token(TOKEN).build()
    
    # Registro de Comandos Generales y Economía
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("perfil", perfil))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("give_money", give_money))
    app.add_handler(CommandHandler("cat", cat))
    
    # Registro de Comandos de Juegos
    app.add_handler(CommandHandler("trabajar", trabajar))
    app.add_handler(CommandHandler("robar", robar))
    app.add_handler(CommandHandler("ruleta", ruleta))
    app.add_handler(CommandHandler("cock_fight", cock_fight))
    app.add_handler(CommandHandler("roll", roll))
    
    # Registro de Comandos Administrativos
    app.add_handler(CommandHandler("set_currency", set_currency))
    app.add_handler(CommandHandler("add_money", add_money))
    app.add_handler(CommandHandler("remove_money", remove_money))
    app.add_handler(CommandHandler("reset_economy", reset_economy))
    app.add_handler(CommandHandler("reset_money", reset_money))
    
    print("🚀 El bot de Telegram está escuchando de forma segura...")
    app.run_polling()

if __name__ == "__main__":
    main()