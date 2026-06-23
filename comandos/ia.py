from google import genai
import os

# Aseguramos que el cliente se inicie correctamente
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

async def chat_con_ia(update, context):
    try:
        user_input = update.message.text
        # Usamos el modelo correcto y validamos la respuesta
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_input,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error en IA: {e}") # Esto aparecerá en los logs de Render
        await update.message.reply_text("Ups, mi cerebro de IA tuvo un pequeño fallo. Intenta de nuevo.")