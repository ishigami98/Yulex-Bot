import os
from postgrest import Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Construimos la URL completa para Postgrest
# La API de Postgrest vive en SUPABASE_URL + /rest/v1
url = f"{SUPABASE_URL}/rest/v1"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Creamos el cliente
supabase = Client(url, headers)

def inicializar_db():
    print("✅ Conectado a Supabase con cliente oficial.")

def obtener_moneda():
    return "💰"

def obtener_o_crear_usuario(telegram_id, username):
    res = supabase.table("usuarios").select("*").eq("telegram_id", telegram_id).execute()
    if not res.data:
        nuevo = {"telegram_id": telegram_id, "username": username, "balance": 500}
        supabase.table("usuarios").insert(nuevo).execute()
        return {"balance": 500, "nuevo": True}
    return {"balance": res.data[0]["balance"], "nuevo": False}

def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    res = supabase.table("usuarios").select("balance").eq("telegram_id", telegram_id).execute()
    balance = res.data[0]["balance"]
    nuevo = balance + cantidad if es_ganancia else balance - cantidad
    supabase.table("usuarios").update({"balance": nuevo}).eq("telegram_id", telegram_id).execute()