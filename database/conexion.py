import os
from supabase import create_client

# Carga las variables desde el entorno de Render
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("¡Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY!")

# Cliente oficial de Supabase (Síncrono)
supabase = create_client(URL, KEY)

def inicializar_db():
    print("Base de datos lista")

# Funciones de utilidad
def obtener_moneda():
    return "💰" 

def obtener_id_por_username(username):
    clean_username = username.replace("@", "").lower()
    res = supabase.table("usuarios").select("telegram_id").eq("username", clean_username).execute()
    if res.data:
        return res.data[0]["telegram_id"]
    return None

async def obtener_o_crear_usuario(telegram_id, username):
    # Quitamos el 'await' porque supabase es síncrono
    res = supabase.table("usuarios").select("*").eq("telegram_id", telegram_id).execute()
    
    if not res.data:
        nuevo = {"telegram_id": telegram_id, "username": username, "balance": 500}
        # Quitamos el 'await'
        supabase.table("usuarios").insert(nuevo).execute()
        return {"balance": 500, "nuevo": True}
    
    return {"balance": res.data[0]["balance"], "nuevo": False}

async def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    # Quitamos el 'await'
    res = supabase.table("usuarios").select("balance").eq("telegram_id", telegram_id).execute()
    
    if not res.data:
        return # O maneja el error si el usuario no existe
        
    balance = res.data[0]["balance"]
    nuevo = balance + cantidad if es_ganancia else balance - cantidad
    
    # Quitamos el 'await'
    supabase.table("usuarios").update({"balance": nuevo}).eq("telegram_id", telegram_id).execute()