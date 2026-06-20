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
        self.resultados = None  # <--- ESTA LÍNEA ES LA CLAVE: Borra el caché antiguo
        if params:
            # Reemplazo seguro de parámetros
            formated_params = tuple(f"'{p}'" if isinstance(p, str) else str(p) for p in params)
            query = query % formated_params

        # ... el resto de tu código de execute sigue igual
            for p in params:
                if isinstance(p, str):
                    # Duplicamos comillas simples internas para evitar romper el SQL literal
                    p_escaped = p.replace("'", "''")
                    formated_params.append(f"'{p_escaped}'")
                elif p is None:
                    formated_params.append("NULL")
                else:
                    formated_params.append(str(p))
            
            # Reemplaza de forma segura cada %s uno por uno
            for param in formated_params:
                query = query.replace("%s", param, 1)
            
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
                print(f"⚠️ Error Supabase: {response.status_code} - {response.text}")
                self.resultados = []
        except Exception as e:
            print(f"❌ Error de red en execute_sql: {e}")
            self.resultados = []
        
        self.index = 0

    # 🛠️ Mapeo robusto: extrae los valores respetando el orden original del JSON/Dict
    def fetchone(self):
        if not self.resultados or self.index >= len(self.resultados):
            return None
        fila = self.resultados[self.index]
        self.index += 1
        
        if isinstance(fila, dict):
            return tuple(fila.values())
        return fila if isinstance(fila, tuple) else (fila,)

    def fetchall(self):
        if not self.resultados:
            return []
        output = []
        for fila in self.resultados[self.index:]:
            if isinstance(fila, dict):
                output.append(tuple(fila.values()))
            elif isinstance(fila, tuple):
                output.append(fila)
            else:
                output.append((fila,))
        self.index = len(self.resultados)
        return output

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
    
    # Esto aparecerá en los logs de Render cada vez que alguien use un comando
    print(f"DEBUG: Usuario {telegram_id} tiene en BD: {user}")
    
    # ... si 'user' es None, el bot crea el usuario. Si 'user' tiene datos, los usa.
    
    # ... el resto sigue igual
    
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