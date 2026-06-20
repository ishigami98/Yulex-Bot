import os
import httpx

# Variables de entorno seguras para la nube
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nkufkghwwbrlesdwbano.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class FalsaConexion:
    def __init__(self):
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    def cursor(self):
        return FalsoCursor(self.headers)
    def commit(self):
        pass
    def close(self):
        pass

class FalsoCursor:
    def __init__(self, headers):
        self.headers = headers
        self.resultados = None
        self.index = 0

    def execute(self, query, params=None):
        if params:
            formated_params = tuple(f"'{p}'" if isinstance(p, str) else str(p) for p in params)
            query = query % formated_params
            
        query_limpia = " ".join(query.split())
        url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
        payload = {"query": query_limpia}
        
        try:
            response = httpx.post(url, json=payload, headers=self.headers, timeout=15.0)
            if response.status_code in [200, 201]:
                self.resultados = response.json()
            else:
                self.resultados = []
        except Exception:
            self.resultados = []
        self.index = 0

    def fetchone(self):
        if self.resultados and self.index < len(self.resultados):
            res = self.resultados[self.index]
            self.index += 1
            return tuple(res.values()) if isinstance(res, dict) else res
        return None

    def fetchall(self):
        if self.resultados:
            return [tuple(res.values()) if isinstance(res, dict) else res for res in self.resultados]
        return []

    def close(self):
        pass

def conectar_db():
    return FalsaConexion()

def inicializar_db():
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 500,
                ganadas INTEGER DEFAULT 0,
                perdidas INTEGER DEFAULT 0,
                ultima_recarga TEXT,
                pollos_ganados INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)
        cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('moneda', '🪙') ON CONFLICT (clave) DO NOTHING")
        conn.commit()
        conn.close()
        print("🔗 Conexión exitosa e inicializada con Supabase por HTTP!")
    except Exception as e:
        print(f"❌ Error al inicializar Supabase: {e}")

# --- Funciones helpers del bot reutilizables ---

def obtener_moneda():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = 'moneda'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "🪙"

def obtener_o_crear_usuario(telegram_id, username):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, ganadas, perdidas, pollos_ganados FROM usuarios WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    
    username_limpio = username.replace("@", "").lower() if username else f"user_{telegram_id}"
    
    if not user:
        cursor.execute(
            "INSERT INTO usuarios (telegram_id, username, balance, ganadas, perdidas, pollos_ganados) VALUES (%s, %s, 500, 0, 0, 0)",
            (telegram_id, username_limpio)
        )
        conn.commit()
        conn.close()
        return {"balance": 500, "ganadas": 0, "perdidas": 0, "pollos": 0, "nuevo": True}
    
    cursor.execute("UPDATE usuarios SET username = %s WHERE telegram_id = %s", (username_limpio, telegram_id))
    conn.commit()
    conn.close()
    return {"balance": user[0], "ganadas": user[1], "perdidas": user[2], "pollos": user[3], "nuevo": False}

def obtener_id_por_username(username):
    conn = conectar_db()
    cursor = conn.cursor()
    username_limpio = username.replace("@", "").lower().strip()
    cursor.execute("SELECT telegram_id FROM usuarios WHERE username = %s", (username_limpio,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    conn = conectar_db()
    cursor = conn.cursor()
    if es_ganancia:
        cursor.execute("""
            UPDATE usuarios 
            SET balance = balance + %s, ganadas = ganadas + %s 
            WHERE telegram_id = %s
        """, (cantidad, cantidad, telegram_id))
    else:
        cursor.execute("""
            UPDATE usuarios 
            SET balance = balance - %s, perdidas = perdidas + %s 
            WHERE telegram_id = %s
        """, (cantidad, cantidad, telegram_id))
    conn.commit()
    conn.close()