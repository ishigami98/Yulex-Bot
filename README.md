# 🎰 Yulex-Bot

Bot de economía y entretenimiento para grupos de Telegram, modular, con Supabase y desplegado gratis en Render.

## ✨ Características

- **💰 Sistema de economía:** registro automático, saldo inicial, leaderboard, transferencias.
- **🎲 Juegos:** ruleta (rojo/negro/verde x14), pelea de gallos, dados, trabajar, robar.
- **🎁 Daily:** reclamo cada 24h con cooldown.
- **🐱 Ocio:** `/cat` con la API de TheCatAPI.
- **😴 AFK:** comando `/afk` o escribiendo `brb`; detecta menciones y respuestas.
- **🛡 Permisos:** comandos de admin y panel para `CREADOR_ID`.
- **☁️ Deploy gratuito:** FastAPI + Uvicorn + ping keep-alive para evitar que Render duerma el servicio.

## 📂 Estructura del Proyecto
.
├── bot.py # Entry point (FastAPI + python-telegram-bot)
├── requirements.txt
├── README.md
├── .gitignore
├── database/
│ └── conexion.py # Cliente de Supabase + helpers
└── comandos/
├── generales.py # /start /help /perfil /daily /leaderboard /cat
├── juegos.py # /trabajar /robar /ruleta /roll /cock_fight
├── admin.py # /add_money /remove_money /reset_*
└── afk.py # /afk + detección automática

## 🗄️ Esquema de Supabase

Crea estas tablas en el SQL Editor de Supabase:

```sql
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS configuracion CASCADE;

CREATE TABLE usuarios (
    telegram_id    BIGINT PRIMARY KEY,
    username       TEXT,
    balance        INTEGER DEFAULT 500,
    ganadas        INTEGER DEFAULT 0,
    perdidas       INTEGER DEFAULT 0,
    ultima_recarga TIMESTAMPTZ,
    ultimo_robo    TIMESTAMPTZ,
    pollos_ganados INTEGER DEFAULT 0
);

CREATE TABLE configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT
);

INSERT INTO configuracion (clave, valor)
VALUES ('moneda', '🪙')
ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor;

🛠 Variables de Entorno

| Variable       | Descripción                                           |
| -------------- | ----------------------------------------------------- |
| TELEGRAM_TOKEN | Token del bot dado por @BotFather.                    |
| SUPABASE_URL   | URL del proyecto (https://xxxxx.supabase.co).         |
| SUPABASE_KEY   | API Key de Supabase (usa la service_role para admin). |
| CREADOR_ID     | Tu Telegram ID numerico para permisos absolutos.      |
| PORT           | Lo asigna Render automáticamente (no tocar).          |


📦 Instalación Local
# 1. Clonar
git clone https://github.com/ishigami98/Yulex-Bot.git
cd Yulex-Bot

# 2. Entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables locales
export TELEGRAM_TOKEN="..."
export SUPABASE_URL="..."
export SUPABASE_KEY="..."
export CREADOR_ID="123456789"

# 5. Ejecutar
python bot.py

☁️ Deploy en Render (plan gratuito)
1. Sube el repo a GitHub.
2. En Render (https://render.com/) crea un Web Service desde el repo.
3. Configuración:
- Build command: pip install -r requirements.txt
- Start command: uvicorn bot:app --host 0.0.0.0 --port $PORT
4. Agrega las variables de entorno (TELEGRAM_TOKEN, SUPABASE_URL, etc.).
5. Importante: Render free duerme el servicio a los 15 min sin tráfico.
Usa cron-job.org (https://cron-job.org/) o UptimeRobot (https://uptimerobot.com/)
para hacer ping a https://tu-app.onrender.com/ cada 5 minutos.

📋 Comandos disponibles
Generales
- /start — Registro y bienvenida
- /help — Lista de comandos
- /perfil — Tu perfil y balance
- /daily — Bono diario
- /leaderboard — Top 10 más ricos
- /cat — Foto random de gato
Juegos
- /trabajar — Gana monedas (cooldown 2h)
- /robar — Roba a otro usuario (cooldown 4h)
- /ruleta <cantidad> <color> — Ruleta rusa
- /roll <cantidad> — Dado 1-6
- /cock_fight <cantidad> — Pelea de gallos
Admin
- /set_currency <símbolo> — Cambia la moneda global
- /add_money @user <cantidad> — Suma al balance
- /remove_money @user <cantidad> — Resta al balance
- /reset_economy CONFIRMAR — Resetea todo
- /reset_money [@user] — Resetea uno o todos
AFK
- /afk [razón] — Marca como AFK
- Escribir brb [razón] — AFK rápido
- Cualquier mensaje — Vuelve automáticamente

🧰 Tech Stack
- Python 3.11+
- python-telegram-bot (https://python-telegram-bot.org/) 21.x
- FastAPI (https://fastapi.tiangolo.com/) + Uvicorn (https://www.uvicorn.org/)
- Supabase (https://supabase.com/) (REST + Postgres)

📝 Licencia
MIT — Úsalo, modifícalo y rómpelo a tu gusto.
Desarrollado con ❤️ por ishigami98 (https://github.com/ishigami98)