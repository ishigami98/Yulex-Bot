import os
from google import genai
from google.genai import types

# Inicializamos el cliente de la nueva librería
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

async def chat_con_ia(update, context):
    mensaje = update.message.text
    try:
        # Llamamos al modelo usando la nueva sintaxis
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"Eres Yulex, un asistente amable, divertido y algo sarcástico. Responde a: {mensaje}"
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error en IA: {e}")
        await update.message.reply_text("Ups, mi cerebro de IA tuvo un pequeño fallo. Intenta de nuevo.")