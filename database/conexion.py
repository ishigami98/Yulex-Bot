import os
from supabase import create_client

# Carga las variables desde el entorno de Render
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("¡Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY!")

# Cliente oficial de Supabase
supabase = create_client(URL, KEY)
def inicializar_db():
    # Esta función solo sirve para mantener la compatibilidad con bot.py
    print("Base de datos lista")
# Funciones de utilidad
def obtener_moneda():
    return "💰" # O el símbolo que prefieras

def obtener_id_por_username(username):
    # Asegúrate de limpiar el nombre
    clean_username = username.replace("@", "").lower()
    res = supabase.table("usuarios").select("telegram_id").eq("username", clean_username).execute()
    if res.data:
        return res.data[0]["telegram_id"]
    return None

async def obtener_o_crear_usuario(telegram_id, username):
    # QUITA el 'await' de aquí
    res = supabase.table("usuarios").select("*").eq("telegram_id", telegram_id).execute()
    
    if not res.data:
        nuevo = {"telegram_id": telegram_id, "username": username, "balance": 500}
        # QUITA el 'await' de aquí
        supabase.table("usuarios").insert(nuevo).execute()
        return {"balance": 500, "nuevo": True}
    
    return {"balance": res.data[0]["balance"], "nuevo": False}

async def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    # QUITA el 'await' de aquí
    res = supabase.table("usuarios").select("balance").eq("telegram_id", telegram_id).execute()
    
    balance = res.data[0]["balance"]
    nuevo = balance + cantidad if es_ganancia else balance - cantidad
    
    # QUITA el 'await' de aquí
    supabase.table("usuarios").update({"balance": nuevo}).eq("telegram_id", telegram_id).execute()