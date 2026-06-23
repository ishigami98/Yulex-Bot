from google import genai
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

async def chat_con_ia(update, context):
    # Esto evita que el bot responda si el mensaje está vacío o es un comando
    if not update.message or not update.message.text:
        return

    try:
        # Usamos el modelo 'gemini-2.0-flash'
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=update.message.text,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        # Logueamos el error para saber qué pasa exactamente en Render
        print(f"DEBUG IA ERROR: {e}") 
        await update.message.reply_text("Perdona, mi cerebro de IA está un poco nublado. Intenta de nuevo.")