import os
import asyncio
from supabase import create_client

# Carga las variables desde el entorno de Render
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("¡Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY!")

# Cliente oficial de Supabase (síncrono)
supabase = create_client(URL, KEY)


def inicializar_db():
    """Verifica que la conexión con Supabase funcione."""
    try:
        supabase.table("usuarios").select("telegram_id").limit(1).execute()
        print("✅ Conexión con Supabase OK")
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")


def obtener_moneda():
    try:
        res = supabase.table("configuracion").select("valor").eq("clave", "moneda").execute()
        if res.data:
            return res.data[0]["valor"]
    except Exception as e:
        print(f"Error en obtener_moneda: {e}")
    return "🪙"  # fallback


def obtener_id_por_username(username: str):
    """Busca el telegram_id de un usuario por su @username (búsqueda insensible a mayúsculas/minúsculas)."""
    clean = username.replace("@", "").strip()
    try:
        # ilike realiza coincidencia insensible a mayúsculas/minúsculas en PostgreSQL
        res = supabase.table("usuarios").select("telegram_id").ilike("username", clean).execute()
        if res.data:
            return res.data[0]["telegram_id"]
    except Exception as e:
        print(f"Error en obtener_id_por_username: {e}")
    return None


def obtener_o_crear_usuario(telegram_id, username):
    """Devuelve el balance del usuario. Lo crea con 500 si no existe."""
    username = username or f"user_{telegram_id}"
    try:
        res = supabase.table("usuarios").select("*").eq("telegram_id", telegram_id).execute()

        if not res.data:
            nuevo = {"telegram_id": telegram_id, "username": username, "balance": 500}
            supabase.table("usuarios").insert(nuevo).execute()
            return {"balance": 500, "nuevo": True}

        return {"balance": res.data[0]["balance"], "nuevo": False}
    except Exception as e:
        print(f"Error en obtener_o_crear_usuario: {e}")
        return {"balance": 0, "nuevo": False}


def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    """Suma o resta al balance del usuario. Devuelve el nuevo saldo o None si falla."""
    try:
        res = supabase.table("usuarios").select("balance").eq("telegram_id", telegram_id).execute()
        if not res.data:
            return None

        balance_actual = res.data[0]["balance"]
        nuevo = balance_actual + cantidad if es_ganancia else balance_actual - cantidad
        supabase.table("usuarios").update({"balance": nuevo}).eq("telegram_id", telegram_id).execute()
        return nuevo
    except Exception as e:
        print(f"Error en actualizar_saldo: {e}")
        return None


# ============ WRAPPERS ASÍNCRONOS (Evitan bloquear el Event Loop) ============
async def async_ejecutar(query):
    """Ejecuta una consulta de Supabase (.execute()) en un hilo de trabajo con asyncio.to_thread."""
    return await asyncio.to_thread(query.execute)


async def async_obtener_moneda():
    return await asyncio.to_thread(obtener_moneda)


async def async_obtener_id_por_username(username: str):
    return await asyncio.to_thread(obtener_id_por_username, username)


async def async_obtener_o_crear_usuario(telegram_id: int, username: str):
    return await asyncio.to_thread(obtener_o_crear_usuario, telegram_id, username)


async def async_actualizar_saldo(telegram_id: int, cantidad: int, es_ganancia: bool = True):
    return await asyncio.to_thread(actualizar_saldo, telegram_id, cantidad, es_ganancia)
