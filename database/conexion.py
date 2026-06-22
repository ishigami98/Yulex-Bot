import os
from postgrest import AsyncPostgrestClient

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
url = f"{SUPABASE_URL}/rest/v1"

# Cliente asíncrono global
supabase = AsyncPostgrestClient(url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})

def inicializar_db():
    print("✅ Base de datos inicializada (modo Async)")

def obtener_moneda():
    return "💰"

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