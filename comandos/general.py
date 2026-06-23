import random
import requests

async def dado(update, context):
    await update.message.reply_text(f"🎲 Has sacado un {random.randint(1, 6)}")

async def gato(update, context):
    url = requests.get("https://api.thecatapi.com/v1/images/search").json()[0]['url']
    await update.message.reply_photo(photo=url)

async def help_cmd(update, context):
    ayuda = "Comandos: /dado, /gato, /abrazo, /beso, /ship, /8ball. ¡Háblame y te responderé como IA!"
    await update.message.reply_text(ayuda)