# comandos/ia.py
from google import genai
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

async def chat_con_ia(update, context):
    try:
        user_input = update.message.text
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_input,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Ups, mi cerebro de IA tuvo un pequeño fallo. Intenta de nuevo.")