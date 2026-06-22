from supabase import create_client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    # Obtener usuario
    response = supabase.table("usuarios").select("balance").eq("telegram_id", telegram_id).execute()
    balance = response.data[0]["balance"]
    
    nuevo_balance = balance + cantidad if es_ganancia else balance - cantidad
    
    # Actualizar usuario
    supabase.table("usuarios").update({"balance": nuevo_balance}).eq("telegram_id", telegram_id).execute()