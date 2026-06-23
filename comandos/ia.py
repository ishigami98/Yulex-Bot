from google import genai
import os

# Asegúrate de usar la librería nueva: google-genai
# Si instalaste 'google-generativeai', cámbialo a 'google-genai' en requirements.txt
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

async def chat_con_ia(update, context):
    if not update.message or not update.message.text:
        return

    try:
        # Imprime esto en los logs de Render para saber qué recibe
        print(f"DEBUG: IA recibiendo mensaje: {update.message.text}")
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=update.message.text,
        )
        
        await update.message.reply_text(response.text)
        
    except Exception as e:
        # ESTO ES LO QUE NECESITO QUE ME DIGAS
        print(f"DEBUG: ERROR CRÍTICO EN IA: {str(e)}")
        await update.message.reply_text("Ups, el cerebro de la IA falló. Revisa los logs de Render.")