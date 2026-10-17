import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from database.conexion import (
    async_actualizar_saldo,
    async_obtener_id_por_username,
    async_ejecutar,
    supabase,
)

logger = logging.getLogger(__name__)

# ID del creador para permisos absolutos
try:
    CREADOR_ID = int(str(os.environ.get("CREADOR_ID", "5235708855")).strip())
except ValueError:
    CREADOR_ID = 5235708855


# ============ PERMISOS ============
async def es_administrador(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Verifica si el usuario tiene privilegios de administrador.
    - CREADOR_ID tiene permisos absolutos (grupos y chat privado).
    - En grupos/supergrupos: verifica si el usuario es creador o administrador del grupo.
    - Si el bot no tiene permisos suficientes para consultar en el grupo, avisa explícitamente.
    - En chat privado: restringe a CREADOR_ID y avisa si no corresponde.
    """
    if not update.effective_user or not update.effective_chat:
        return False

    user_id = update.effective_user.id
    if user_id == CREADOR_ID:
        return True

    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            if member.status in ["administrator", "creator"]:
                return True
            else:
                await update.effective_message.reply_text("❌ No tienes permisos de administrador en este grupo.")
                return False
        except TelegramError as e:
            err_msg = str(e).lower()
            logger.error(f"Error verificando admin en chat {chat.id} para usuario {user_id}: {e}")
            if "admin_required" in err_msg or "not enough rights" in err_msg or "chat_admin_required" in err_msg:
                await update.effective_message.reply_text(
                    "⚠️ El bot necesita ser administrador en este grupo para verificar los permisos de los miembros."
                )
            else:
                await update.effective_message.reply_text("❌ Error al verificar permisos en Telegram.")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en es_administrador: {e}")
            await update.effective_message.reply_text("❌ Error al verificar permisos.")
            return False
    else:
        # Chat privado: solo el creador del bot tiene acceso administrativo
        await update.effective_message.reply_text(
            "❌ No tienes permisos. En chat privado, los comandos de administración solo están disponibles para el creador del bot."
        )
        return False


# ============ SET CURRENCY ============
async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        return
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: /set_currency <símbolo> o /set_currency default"
        )
        return

    nuevo_simbolo = "🪙" if context.args[0].lower() == "default" else context.args[0]

    try:
        res = await async_ejecutar(
            supabase.table("configuracion").select("clave").eq("clave", "moneda")
        )
        if res.data:
            await async_ejecutar(
                supabase.table("configuracion").update({"valor": nuevo_simbolo}).eq("clave", "moneda")
            )
        else:
            await async_ejecutar(
                supabase.table("configuracion").insert({"clave": "moneda", "valor": nuevo_simbolo})
            )
        await update.message.reply_text(f"✅ Símbolo global cambiado a: {nuevo_simbolo}")
    except Exception as e:
        logger.error(f"Error en set_currency: {e}")
        await update.message.reply_text("❌ Error guardando el símbolo en la base de datos.")


# ============ ADD MONEY ============
async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
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

    target_id = await async_obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text(f"❌ Usuario {target_user} no encontrado en la base de datos.")
        return

    nuevo = await async_actualizar_saldo(target_id, cantidad, es_ganancia=True)
    if nuevo is None:
        await update.message.reply_text("❌ Error actualizando el saldo.")
        return
    await update.message.reply_text(
        f"✅ Se añadieron {cantidad} al saldo de {target_user}.\nNuevo saldo: {nuevo}"
    )


# ============ REMOVE MONEY ============
async def remove_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
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

    target_id = await async_obtener_id_por_username(target_user)
    if not target_id:
        await update.message.reply_text(f"❌ Usuario {target_user} no encontrado en la base de datos.")
        return

    nuevo = await async_actualizar_saldo(target_id, cantidad, es_ganancia=False)
    if nuevo is None:
        await update.message.reply_text("❌ Error actualizando el saldo.")
        return
    await update.message.reply_text(
        f"📉 Se retiraron {cantidad} del saldo de {target_user}.\nNuevo saldo: {nuevo}"
    )


# ============ RESET ECONOMY ============
async def reset_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_administrador(update, context):
        return

    if not (len(context.args) >= 1 and context.args[0].upper() == "CONFIRMAR"):
        await update.message.reply_text(
            "⚠️ <b>¡CUIDADO!</b> Esto dejará a TODOS los usuarios en 0.\n"
            "Si estás seguro, ejecuta:\n"
            "<code>/reset_economy CONFIRMAR</code>",
            parse_mode="HTML",
        )
        return

    try:
        await async_ejecutar(
            supabase.table("usuarios")
            .update({"balance": 0, "ganadas": 0, "perdidas": 0, "pollos_ganados": 0})
            .neq("telegram_id", 0)
        )
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
    if context.args:
        if not await es_administrador(update, context):
            return
        target_user = context.args[0]
        target_id = await async_obtener_id_por_username(target_user)
        if not target_id:
            await update.message.reply_text(f"❌ Usuario {target_user} no encontrado.")
            return
        try:
            await async_ejecutar(
                supabase.table("usuarios")
                .update({"balance": 500, "ganadas": 0, "perdidas": 0})
                .eq("telegram_id", target_id)
            )
            await update.message.reply_text(
                f"🔄 Se reinició el dinero de {target_user} a 500."
            )
        except Exception as e:
            logger.error(f"Error en reset_money admin: {e}")
            await update.message.reply_text("❌ Error al reiniciar.")
        return

    # Si no pasa argumentos, reset propio del usuario que llama
    try:
        await async_ejecutar(
            supabase.table("usuarios")
            .update({"balance": 500, "ganadas": 0, "perdidas": 0})
            .eq("telegram_id", user_id)
        )
        await update.message.reply_text(
            "🔄 Reiniciaste tu dinero a 500 y tus estadísticas a 0."
        )
    except Exception as e:
        logger.error(f"Error en reset_money self: {e}")
        await update.message.reply_text("❌ Error al reiniciar tu perfil.")


# ============ GIVE MONEY ============
async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Se mantiene la restricción de admin como está actualmente según instrucción C.5
    if not await es_administrador(update, context):
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

    target_id = await async_obtener_id_por_username(target_username)
    if not target_id:
        await update.message.reply_text(f"❌ Usuario {target_username} no encontrado en la base de datos.")
        return

    nuevo = await async_actualizar_saldo(target_id, cantidad, es_ganancia=True)
    if nuevo is None:
        await update.message.reply_text("❌ Error al enviar el dinero.")
        return
    await update.message.reply_text(
        f"✅ Se enviaron {cantidad} a {target_username}.\nSaldo actual: {nuevo}"
    )
