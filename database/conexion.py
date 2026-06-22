import os
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BASE_URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def inicializar_db():
    print("✅ Base de datos inicializada (modo HTTP directo)")

def obtener_moneda():
    return "💰"

def obtener_o_crear_usuario(telegram_id, username):
    r = httpx.get(
        f"{BASE_URL}/usuarios?telegram_id=eq.{telegram_id}&select=*",
        headers=HEADERS
    )
    data = r.json()
    
    if not data:
        # No existe → lo creamos
        httpx.post(
            f"{BASE_URL}/usuarios",
            headers=HEADERS,
            json={"telegram_id": telegram_id, "username": username, "balance": 500}
        )
        return {"balance": 500, "ganadas": 0, "perdidas": 0, "pollos": 0}
    
    u = data[0]
    return {
        "balance": u["balance"],
        "ganadas": u.get("ganadas", 0),
        "perdidas": u.get("perdidas", 0),
        "pollos": u.get("pollos_ganados", 0)
    }

def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    # Traemos el balance actual
    r = httpx.get(
        f"{BASE_URL}/usuarios?telegram_id=eq.{telegram_id}&select=balance",
        headers=HEADERS
    )
    balance_actual = r.json()[0]["balance"]
    
    nuevo = balance_actual + cantidad if es_ganancia else balance_actual - cantidad
    
    httpx.patch(
        f"{BASE_URL}/usuarios?telegram_id=eq.{telegram_id}",
        headers=HEADERS,
        json={"balance": nuevo}
    )

def obtener_id_por_username(username):
    username_clean = username.replace("@", "").lower()
    r = httpx.get(
        f"{BASE_URL}/usuarios?username=eq.{username_clean}&select=telegram_id",
        headers=HEADERS
    )
    data = r.json()
    return data[0]["telegram_id"] if data else None
