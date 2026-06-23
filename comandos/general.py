import random
import requests
from telegram import Update
from telegram.ext import ContextTypes

async def ball8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = [
        "Es cierto.", "Es decididamente así.", "Sin lugar a dudas.",
        "Sí, definitivamente.", "Puedes confiar en ello.", "Tal como lo veo, sí.",
        "Lo más probable.", "El panorama es bueno.", "Sí.", "Las señales apuntan a que sí.",
        "La respuesta es confusa, intenta de nuevo.", "Pregunta de nuevo más tarde.", "Mejor no decirte ahora.",
        "No puedo predecirlo ahora.", "Concéntrate y vuelve a preguntar.",
        "No cuentes con ello.", "Mi respuesta es no.", "Mis fuentes dicen que no.",
        "El panorama no es muy bueno.", "Muy dudoso."
    ]
    
    if not context.args:
        await update.message.reply_text("¡Por favor, haz una pregunta! 🎱")
        return

    await update.message.reply_text(f"🎱 {random.choice(answers)}")

async def dado(update, context):
    await update.message.reply_text(f"🎲 Has sacado un {random.randint(1, 6)}")

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hacemos la petición a la API
    response = requests.get("https://api.thecatapi.com/v1/images/search").json()
    url = response[0]['url']
    
    # Enviamos el mensaje con el emoji y la foto
    # Usamos parse_mode 'Markdown' por si quieres poner algo en negrita en el futuro
    await update.message.reply_photo(
        photo=url, 
        caption="Toma un gatito 🐱"
    )

async def help_cmd(update, context):
    help_text = (
        "✨ **Yulex Bot - Menú de Ayuda** ✨\n\n"
        "📜 **Generales**\n"
        "/start - Saludo inicial\n"
        "/dado - Lanza un dado\n"
        "/cat - Imagen de un gatito\n"
        "/8ball - Consulta a la bola mágica\n\n"
        "💖 **Interacción**\n"
        "/kiss @usuario - Besa a alguien\n"
        "/abrazo @usuario - Abraza a alguien\n"
        "/ship @usuario - Mira tu compatibilidad\n\n"
        "🤖 *Escríbeme cualquier cosa para chatear con la IA.*"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')