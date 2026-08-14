import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.conexion import actualizar_saldo, obtener_id_por_username, supabase

logger = logging.getLogger(__name__)

# ID del creador para permisos absolutos
CREADOR_ID = int(os.environ.get("CREADOR_ID", 5235708855))


# ============ PERMISOS ============
async def es_administrador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == CREADOR_ID:
        return True
    try:
        if update.effective_chat.type in ["group", "supergroup"]:
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            if member.status in ["administrator", "creator"]:
                return True
    except Exception as e:
        logger.error(f"Error verificando admin: {e}")
    return False


# ============ SET CURRENCY ============
async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: /set_currency <símbolo> o /set_currency default"
        )
        return

    nuevo_simbolo = "🪙" if context.args[0].lower() == "default" else context.args[0]

    try:
        # Guarda/actualiza en la tabla configuracion
        res = supabase.table("configuracion").select("clave").eq("clave", "moneda").execute()
        if res.data:
            supabase.table("configuracion").update(
                {"valor": nuevo_simbolo}
            ).eq("clave", "moneda").execute()
        else:
            supabase.table("configuracion").insert(
                {"clave": "moneda", "valor": nuevo_simbolo}
            ).execute()
        await update.message.reply_text(f"✅ Símbolo global cambiado a: {nuevo_simbolo}")
    except Exception as e:
        logger.error(f"Error en set_currency: {e}")
        await update.message.reply_text("❌ Error guardando el símbolo.")


# ============ ADD MONEY ============
async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /add_money @usuario <cantidad>")
        return

    target_user = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ La cantidad debe ser un número entero.")
        return

    if cantidad <= 0:
        await update.message.reply_text("❌ La cantidad debe ser positiva.")
        return

    target_id = obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return

    nuevo = actualizar_saldo(target_id, cantidad, es_ganancia=True)
    if nuevo is None:
        await update.message.reply_text("❌ Error actualizando el saldo.")
        return
    await update.message.reply_text(
        f"✅ Se añadieron {cantidad} al saldo de {target_user}.\nNuevo saldo: {nuevo}"
    )


# ============ REMOVE MONEY ============
async def remove_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /remove_money @usuario <cantidad>")
        return

    target_user = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ La cantidad debe ser un número entero.")
        return

    if cantidad <= 0:
        await update.message.reply_text("❌ La cantidad debe ser positiva.")
        return

    target_id = obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return

    nuevo = actualizar_saldo(target_id, cantidad, es_ganancia=False)
    if nuevo is None:
        await update.message.reply_text("❌ Error actualizando el saldo.")
        return
    await update.message.reply_text(
        f"📉 Se retiraron {cantidad} del saldo de {target_user}.\nNuevo saldo: {nuevo}"
    )


# ============ RESET ECONOMY ============
async def reset_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No eres administrador.")
        return

    # Doble confirmación: si el segundo argumento no es "CONFIRMAR", pedimos confirmación
    if not (len(context.args) >= 1 and context.args[0].upper() == "CONFIRMAR"):
        await update.message.reply_text(
            "⚠️ <b>¡CUIDADO!</b> Esto dejará a TODOS los usuarios en 0.\n"
            "Si estás seguro, ejecuta:\n"
            "<code>/reset_economy CONFIRMAR</code>",
            parse_mode="HTML",
        )
        return

    try:
        # nq("telegram_id", 0) → todos los usuarios
        supabase.table("usuarios").update(
            {"balance": 0, "ganadas": 0, "perdidas": 0, "pollos_ganados": 0}
        ).neq("telegram_id", 0).execute()
        await update.message.reply_text(
            "🚨 <b>LA ECONOMÍA HA SIDO REINICIADA</b>.\n"
            "Todos los saldos y estadísticas quedaron en 0.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error en reset_economy: {e}")
        await update.message.reply_text("❌ Error al reiniciar la economía.")


# ============ RESET MONEY ============
async def reset_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Si es admin y pasa un @usuario, resetea a ese usuario
    if context.args and await es_administrador(update, context):
        target_user = context.args[0]
        target_id = obtener_id_por_username(target_user)
        if not target_id:
            await update.message.reply_text("❌ Usuario no encontrado.")
            return
        try:
            supabase.table("usuarios").update(
                {"balance": 500, "ganadas": 0, "perdidas": 0}
            ).eq("telegram_id", target_id).execute()
            await update.message.reply_text(
                f"🔄 Se reinició el dinero de {target_user} a 500."
            )
        except Exception as e:
            logger.error(f"Error en reset_money admin: {e}")
            await update.message.reply_text("❌ Error al reiniciar.")
        return

    # Si no, reset propio
    try:
        supabase.table("usuarios").update(
            {"balance": 500, "ganadas": 0, "perdidas": 0}
        ).eq("telegram_id", user_id).execute()
        await update.message.reply_text(
            "🔄 Reiniciaste tu dinero a 500 y tus estadísticas a 0."
        )
    except Exception as e:
        logger.error(f"Error en reset_money self: {e}")
        await update.message.reply_text("❌ Error al reiniciar.")


# ============ GIVE MONEY ============
async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /give_money <@usuario> <cantidad>")
        return

    target_username = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ La cantidad debe ser un número entero.")
        return

    if cantidad <= 0:
        await update.message.reply_text("❌ La cantidad debe ser positiva.")
        return

    target_id = obtener_id_por_username(target_username)
    if not target_id:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return

    nuevo = actualizar_saldo(target_id, cantidad, es_ganancia=True)
    if nuevo is None:
        await update.message.reply_text("❌ Error al enviar el dinero.")
        return
    await update.message.reply_text(
        f"✅ Se enviaron {cantidad} a {target_username}.\nSaldo actual: {nuevo}"
    )
