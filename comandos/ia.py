import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

async def chat_con_ia(update, context):
    mensaje = update.message.text
    try:
        response = model.generate_content(f"Eres Yulex, un asistente amable, divertido y algo sarcástico. Responde a: {mensaje}")
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Ups, mi cerebro de IA tuvo un pequeño fallo. Intenta de nuevo.")