import random
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.conexion import (
    obtener_o_crear_usuario,
    obtener_moneda,
    actualizar_saldo,
    supabase,
)

logger = logging.getLogger(__name__)

# ============ CONSTANTES ============
COOLDOWN_TRABAJAR = timedelta(hours=8)
COOLDOWN_CRIMEN = timedelta(hours=4)
APUESTA_MINIMA = 10


# ============ HELPERS ============
def _perfil(user_id, username):
    """Trae balance + cooldowns en una sola consulta."""
    info = obtener_o_crear_usuario(user_id, username)
    username = username or f"user_{user_id}"
    try:
        res = supabase.table("usuarios").select("*").eq("telegram_id", user_id).execute()
        if res.data:
            row = res.data[0]
            return {
                "username": row.get("username", username),
                "balance": row.get("balance", 0),
                "ultima_recarga": row.get("ultima_recarga"),
                "ultimo_robo": row.get("ultimo_robo"),
                "pollos_ganados": row.get("pollos_ganados", 0),
            }
    except Exception as e:
        logger.error(f"Error en _perfil: {e}")
    return {
        "username": username,
        "balance": info.get("balance", 0),
        "ultima_recarga": None,
        "ultimo_robo": None,
        "pollos_ganados": 0,
    }


def _puede_hacer(ultimo_str, cooldown):
    """Devuelve True si ya pasó el cooldown."""
    if not ultimo_str:
        return True
    try:
        ultimo = datetime.fromisoformat(ultimo_str)
        return (datetime.utcnow() - ultimo) >= cooldown
    except (ValueError, TypeError):
        return True


def _restante(ultimo_str, cooldown):
    """Devuelve string con el tiempo restante para el cooldown."""
    if not ultimo_str:
        return None
    try:
        ultimo = datetime.fromisoformat(ultimo_str)
        diff = cooldown - (datetime.utcnow() - ultimo)
        if diff.total_seconds() <= 0:
            return None
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)
        return f"{horas}h {minutos}m"
    except (ValueError, TypeError):
        return None


# ============ TRABAJAR (cada 8h) ============
async def trabajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        info = _perfil(user.id, user.username)
        m = obtener_moneda()

        if not _puede_hacer(info["ultima_recarga"], COOLDOWN_TRABAJAR):
            restante = _restante(info["ultima_recarga"], COOLDOWN_TRABAJAR)
            await update.message.reply_text(
                f"⏳ Ya trabajaste. Vuelve en {restante}."
            )
            return

        paga = random.randint(80, 250)
        nuevo = actualizar_saldo(user.id, paga, es_ganancia=True)
        supabase.table("usuarios").update(
            {"ultima_recarga": datetime.utcnow().isoformat()}
        ).eq("telegram_id", user.id).execute()

        frases = [
            "Le lavaste el auto al jefe 👔",
            "Vendiste limonada en la calle 🍋",
            "Hiciste un stream de programación 💻",
            "Tradujiste un manual técnico 📚",
            "Reparaste una PC gamer 🖥️",
            "Hiciste entregas a domicilio 🛵",
            "Cuidaste al perro del vecino 🐕",
        ]
        frase = random.choice(frases)
        await update.message.reply_text(
            f"💼 {frase}\n\nGanaste {paga} {m}.\nSaldo actual: {nuevo} {m}"
        )

    except Exception as e:
        logger.error(f"Error en trabajar: {e}")
        await update.message.reply_text("❌ Error al trabajar. Inténtalo más tarde.")

# ============ CRIMEN (cada 4h, sin reply) ============
CRIMENES = [
    # (texto, exito_msg_template, fallo_msg_template, paga_min, paga_max, multa_min, multa_max)
    ("asaltar el banco 🏦",       "robaste del banco",        "te atraparon en el banco",          200, 600,  80, 200),
    ("robar a una abuelita 👵",   "le quitaste la cartera",   "la abuelita te dio con el bastón",  50, 150,  30, 80),
    ("hackear una cuenta 💻",     "hackeaste la cuenta",      "te rastrearon las IPs",             100, 350,  60, 150),
    ("vender cosas sospechosas 📦", "vendiste la mercancía",  "la policía confiscó todo",           80, 250,  40, 100),
    ("estafar por internet 🎭",  "te creyeron todo",         "te reportaron y baneaste",          60, 200,  30, 90),
    ("robar un auto 🚗",          "te lo llevaste",           "la policía te siguió hasta tu casa", 250, 700, 100, 250),
    ("vender drogas en la escuela 🚬", "vendiste todo",       "el director te entregó a la poli",  150, 400,  80, 180),
    ("romper un buzón de correo 📮", "encontraste dinero",    "te mordió un perro guardián",         20, 80,   10, 40),
    ("asaltar una tienda 🏪",     "te llevaste la caja",      "el dueño te disparó",               120, 380,  70, 160),
    ("clonar tarjetas 💳",         "te quedaron 50 lucas",    "el banco congeló tu cuenta",        180, 500,  90, 200),
]

async def crimen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        info = _perfil(user.id, user.username)
        m = obtener_moneda()

        if not _puede_hacer(info["ultimo_robo"], COOLDOWN_CRIMEN):
            restante = _restante(info["ultimo_robo"], COOLDOWN_CRIMEN)
            await update.message.reply_text(
                f"⏳ La policía te vigila. Vuelve en {restante}."
            )
            return

        accion, exito_tpl, fallo_tpl, g_min, g_max, p_min, p_max = random.choice(CRIMENES)
        exito = random.random() < 0.5  # 50% probabilidad

        if exito:
            ganancia = random.randint(g_min, g_max)
            nuevo = actualizar_saldo(user.id, ganancia, es_ganancia=True)
            await update.message.reply_text(
                f"🦹 <b>Intento: {accion}</b>\n\n"
                f"✅ {exito_tpl} y ganaste {ganancia} {m}.\n"
                f"Saldo actual: {nuevo} {m}",
                parse_mode="HTML",
            )
        else:
            multa = random.randint(p_min, p_max)
            # Si no le alcanza para pagar la multa, queda en 0
            saldo_actual = info["balance"]
            multa_real = min(multa, saldo_actual)
            actualizar_saldo(user.id, multa_real, es_ganancia=False)
            await update.message.reply_text(
                f"🦹 <b>Intento: {accion}</b>\n\n"
                f"❌ {fallo_tpl}. Pagaste {multa_real} {m} de multa.\n"
                f"Saldo actual: {max(0, saldo_actual - multa_real)} {m}",
                parse_mode="HTML",
            )

        supabase.table("usuarios").update(
            {"ultimo_robo": datetime.utcnow().isoformat()}
        ).eq("telegram_id", user.id).execute()

    except Exception as e:
        logger.error(f"Error en crimen: {e}")
        await update.message.reply_text("❌ Error en el crimen.")


# ============ RULETA (rusa) ============
async def ruleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        m = obtener_moneda()

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "🎰 Uso: /ruleta <cantidad> <color>\n"
                "Colores: 🔴 rojo | ⚫ negro | 🟢 verde (paga x14)"
            )
            return

        try:
            apuesta = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ La apuesta debe ser un número.")
            return

        if apuesta < APUESTA_MINIMA:
            await update.message.reply_text(f"❌ Apuesta mínima: {APUESTA_MINIMA} {m}.")
            return

        color = context.args[1].lower()
        if color not in ("rojo", "negro", "verde"):
            await update.message.reply_text("❌ Color inválido. Usa: rojo, negro o verde.")
            return

        info = _perfil(user.id, user.username)
        if info["balance"] < apuesta:
            await update.message.reply_text(
                f"❌ No te alcanza. Saldo: {info['balance']} {m}."
            )
            return

        # Resultado: 0-14 rojo, 15-29 negro, 30 verde (1/30)
        n = random.randint(0, 30)
        if n < 15:
            color_real = "rojo"
            emoji = "🔴"
        elif n < 30:
            color_real = "negro"
            emoji = "⚫"
        else:
            color_real = "verde"
            emoji = "🟢"

        if color == color_real:
            multiplicador = 14 if color_real == "verde" else 2
            premio = apuesta * multiplicador
            nuevo = actualizar_saldo(user.id, premio, es_ganancia=True)
            # Sumamos la apuesta que ya se restó mentalmente (en realidad no se resta, se gana el premio entero)
            await update.message.reply_text(
                f"🎉 ¡Acertaste! Salió {emoji} {color_real}.\n"
                f"Ganaste {premio} {m}. Saldo: {nuevo} {m}"
            )
        else:
            actualizar_saldo(user.id, apuesta, es_ganancia=False)
            info = _perfil(user.id, user.username)
            await update.message.reply_text(
                f"💀 Salió {emoji} {color_real}. Perdiste {apuesta} {m}.\n"
                f"Saldo: {info['balance']} {m}"
            )

    except Exception as e:
        logger.error(f"Error en ruleta: {e}")
        await update.message.reply_text("❌ Error en la ruleta.")


# ============ ROLL (eliges número) ============
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        m = obtener_moneda()

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                f"🎲 Uso: /roll <cantidad> <número 1-6>\n"
                f"Acertar paga x1.5. Falla pierdes lo apostado."
            )
            return

        try:
            apuesta = int(context.args[0])
            eleccion = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ La apuesta y el número deben ser enteros.")
            return

        if eleccion < 1 or eleccion > 6:
            await update.message.reply_text("❌ El número debe ser del 1 al 6.")
            return
        if apuesta < APUESTA_MINIMA:
            await update.message.reply_text(f"❌ Apuesta mínima: {APUESTA_MINIMA} {m}.")
            return

        info = _perfil(user.id, user.username)
        if info["balance"] < apuesta:
            await update.message.reply_text(
                f"❌ No te alcanza. Saldo: {info['balance']} {m}."
            )
            return

        dado = random.randint(1, 6)
        if dado == eleccion:
            premio = int(apuesta * 1.5)
            nuevo = actualizar_saldo(user.id, premio, es_ganancia=True)
            await update.message.reply_text(
                f"🎲 Sacaste <b>{dado}</b>. ¡Acertaste!\n"
                f"Ganaste {premio} {m}. Saldo: {nuevo} {m}",
                parse_mode="HTML",
            )
        else:
            actualizar_saldo(user.id, apuesta, es_ganancia=False)
            info = _perfil(user.id, user.username)
            await update.message.reply_text(
                f"🎲 Sacaste <b>{dado}</b>. Apostaste al {eleccion}.\n"
                f"Perdiste {apuesta} {m}. Saldo: {info['balance']} {m}",
                parse_mode="HTML",
            )

    except Exception as e:
        logger.error(f"Error en roll: {e}")
        await update.message.reply_text("❌ Error en el dado.")

# ============ COCK FIGHT (pelea de gallos) ============
async def cock_fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia una pelea. Pone un callback con el resultado."""
    try:
        user = update.effective_user
        info = _perfil(user.id, user.username)
        m = obtener_moneda()

        if not context.args:
            await update.message.reply_text("🐓 Uso: /cock_fight <cantidad>")
            return
        try:
            apuesta = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ La apuesta debe ser un número.")
            return

        if apuesta < APUESTA_MINIMA:
            await update.message.reply_text(f"❌ Apuesta mínima: {APUESTA_MINIMA} {m}.")
            return
        if info["balance"] < apuesta:
            await update.message.reply_text(
                f"❌ No te alcanza. Saldo: {info['balance']} {m}."
            )
            return

        # Gallos con stats aleatorios
        gallos = [
            ("🔥 El Rojazo", random.randint(40, 100)),
            ("⚡ El Rayo", random.randint(40, 100)),
            ("🧊 El Hielo", random.randint(40, 100)),
        ]
        ganador_idx = max(range(len(gallos)), key=lambda i: gallos[i][1])

        keyboard = [
            [InlineKeyboardButton(
                f"{g[0]} ({g[1]} ATK)",
                callback_data=f"cock:{ganador_idx}:{apuesta}:{user.id}"
            )]
            for g in gallos
        ]
        # Truco: la opción del ganador está marcada; el jugador "elige" y si acierta gana.
        # Para hacerlo simple, le decimos cuál ganó después.
        await update.message.reply_text(
            "🐓 <b>¡Pelea de gallos!</b>\n"
            "Mira los stats y espera el resultado...",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.error(f"Error en cock_fight: {e}")
        await update.message.reply_text("❌ Error iniciando la pelea.")


# ============ CALLBACK HANDLER ============
async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        if not query.data or not query.data.startswith("cock:"):
            return

        _, ganador_idx, apuesta, user_id = query.data.split(":")
        ganador_idx = int(ganador_idx)
        apuesta = int(apuesta)
        user_id = int(user_id)

        if query.from_user.id != user_id:
            await query.answer("Esta pelea no es tuya.", show_alert=True)
            return

        m = obtener_moneda()
        # En este diseño simple, si presionas el ganador, ganas.
        # Si presionas otro, pierdes. (El usuario ve cuál es el fuerte por los stats).
        # Para que sea justo sin trampas, lo hacemos 50/50 al presionar.
        if random.random() < 0.5:
            premio = apuesta * 2
            nuevo = actualizar_saldo(user_id, premio, es_ganancia=True)
            supabase.table("usuarios").update(
                {"pollos_ganados": supabase.rpc("increment_pollos", {"uid": user_id}).execute()}
            ).eq("telegram_id", user_id).execute() if False else None
            # Lo anterior es complejo. Simplificamos:
            try:
                res = supabase.table("usuarios").select("pollos_ganados").eq("telegram_id", user_id).execute()
                actual = res.data[0].get("pollos_ganados", 0) if res.data else 0
                supabase.table("usuarios").update(
                    {"pollos_ganados": actual + 1}
                ).eq("telegram_id", user_id).execute()
            except Exception as e:
                logger.error(f"Error actualizando pollos_ganados: {e}")

            await query.edit_message_text(
                f"🐓 ¡Tu gallo ganó la pelea!\n"
                f"Premio: {premio} {m}. Saldo: {nuevo} {m}"
            )
        else:
            actualizar_saldo(user_id, apuesta, es_ganancia=False)
            info = _perfil(user_id, None)
            await query.edit_message_text(
                f"🐓 Tu gallo perdió.\n"
                f"Perdiste {apuesta} {m}. Saldo: {info['balance']} {m}"
            )

    except Exception as e:
        logger.error(f"Error en manejar_callback: {e}")
        try:
            await query.edit_message_text("❌ Error procesando la pelea.")
        except Exception:
            pass
