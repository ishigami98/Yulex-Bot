import os
import httpx

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
        self.resultados = None
        if params:
            formated_params = []
            for p in params:
                val = f"'{p}'" if isinstance(p, str) else str(p)
                formated_params.append(val)
            query = query % tuple(formated_params)
            
        query_limpia = " ".join(query.split())
        if not query_limpia.rstrip().endswith(";"):
            query_limpia += ";"
        
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
        if not self.resultados or self.index >= len(self.resultados):
            return None
        fila = self.resultados[self.index]
        self.index += 1
        return tuple(fila.values()) if isinstance(fila, dict) else (fila if isinstance(fila, tuple) else (fila,))

def conectar_db():
    return FalsaConexion()

def obtener_o_crear_usuario(telegram_id, username):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, ganadas, perdidas, pollos_ganados FROM usuarios WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO usuarios (telegram_id, username, balance) VALUES (%s, %s, 500)", (telegram_id, username))
        conn.commit()
        return {"balance": 500, "ganadas": 0, "perdidas": 0, "pollos": 0}
    return {"balance": user[0], "ganadas": user[1], "perdidas": user[2], "pollos": user[3]}

def actualizar_saldo(telegram_id, cantidad, es_ganancia=True):
    conn = conectar_db()
    cursor = conn.cursor()
    if es_ganancia:
        cursor.execute("UPDATE usuarios SET balance = balance + %s WHERE telegram_id = %s", (cantidad, telegram_id))
    else:
        cursor.execute("UPDATE usuarios SET balance = balance - %s WHERE telegram_id = %s", (cantidad, telegram_id))
    conn.commit()
    
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
        conn.commit()
        conn.close()
        print("🔗 Conexión exitosa e inicializada con Supabase por HTTP!")
    except Exception as e:
        print(f"❌ Error al inicializar Supabase: {e}")