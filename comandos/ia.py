from google import genai
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

async def chat_con_ia(update, context):
    if not update.message or not update.message.text:
        return

    try:
        print(f"DEBUG: IA recibiendo mensaje: {update.message.text}")
        
        # Ejecutar la llamada síncrona en un hilo separado
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=update.message.text,
        )
        
        await update.message.reply_text(response.text)
        
    except Exception as e:
        print(f"DEBUG: ERROR CRÍTICO EN IA: {str(e)}")
        await update.message.reply_text("Ups, el cerebro de la IA falló. Revisa los logs de Render.")
