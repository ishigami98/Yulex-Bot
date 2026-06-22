import os
from postgrest import AsyncPostgrestClient

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# La URL de Postgrest es la dirección del REST API
url = f"{SUPABASE_URL}/rest/v1"

# Creamos el cliente pasando solo la URL y el token
# La librería se encarga de los headers internamente
supabase = AsyncPostgrestClient(url, SUPABASE_KEY)

def inicializar_db():
    print("✅ Base de datos inicializada (Conexión asíncrona)")

def obtener_moneda():
    return "💰"

# NOTA: Como ahora usamos postgrest nativo (asíncrono), 
# todas las funciones que llaman a supabase.table(...) 
# DEBEN ser 'async' y usar 'await'.

async def obtener_o_crear_usuario(telegram_id, username):
    # Agregamos 'await' antes de cada llamada a supabase
    res = await supabase.table("usuarios").select("*").eq("telegram_id", telegram_id).execute()
    
    if not res.data:
        nuevo = {"telegram_id": telegram_id, "username": username, "balance": 500}
        await supabase.table("usuarios").insert(nuevo).execute()
        return {"balance": 500, "nuevo": True}
    
    return {"balance": res.data[0]["balance"], "nuevo": False}

async def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    # Agregamos 'await'
    res = await supabase.table("usuarios").select("balance").eq("telegram_id", telegram_id).execute()
    
    balance = res.data[0]["balance"]
    nuevo = balance + cantidad if es_ganancia else balance - cantidad
    
    # Agregamos 'await'
    await supabase.table("usuarios").update({"balance": nuevo}).eq("telegram_id", telegram_id).execute()