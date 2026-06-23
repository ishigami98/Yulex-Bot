import random
from telegram import Update
from telegram.ext import ContextTypes

# Diccionario de imágenes (puedes buscar más links en Giphy o Tenor)
IMAGES = {
    "slap": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ4eG9pZzNqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3XlJ4fO075h0u3FpW6/giphy.gif"],
    "spank": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ4eG9pZzNqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/l2Sq5GffrciZlH25W/giphy.gif"],
    "kill": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ4eG9pZzNqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/xT9KVnKfPbSgqpHt2o/giphy.gif"],
    "revive": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ4eG9pZzNqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqZ2JpbmZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/l41lTjJp90YyH2b2U/giphy.gif"]
}

async def get_target(update: Update):
    # 1. Si respondió a un mensaje, ese es el objetivo
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    
    # 2. Si mencionó a alguien con @usuario
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'mention':
                # Buscamos el ID del usuario mencionado en la lista de entidades
                # Nota: Esto requiere que el usuario esté en la caché del bot
                return entity.user # Esto funciona si el usuario es miembro del grupo
    
    return None

async def generic_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action_type: str, phrases: list):
    target = await get_target(update)
    
    # Validación: Si no mencionó a nadie o si intenta interactuar consigo mismo o con el bot
    if not target or target.id == update.effective_user.id or target.id == context.bot.id:
        await update.message.reply_text("¡Aléjate por favor!")
        return

    user = update.effective_user.first_name
    target_name = target.first_name
    
    text = random.choice(phrases).format(user=user, target=target_name)
    await update.message.reply_animation(animation=random.choice(IMAGES[action_type]), caption=text)
# Funciones finales
async def slap(u, c): await generic_action(u, c, "slap", ["{user} abofeteó a {target} muy fuerte!", "{user} le dio una bofetada a {target}."])
async def spank(u, c): await generic_action(u, c, "spank", ["{user} le dio una nalgada a {target}!", "{target} recibió una nalgada traviesa de {user}."])
async def kill(u, c): await generic_action(u, c, "kill", ["{user} ha terminado con {target}...", "{user} envió a {target} al reino de las sombras."])
async def revive(u, c): await generic_action(u, c, "revive", ["{user} revivió a {target}!", "{target} ha sido revivido por {user}."])

async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Identificar al objetivo (quien responde o quien es mencionado)
    target = None
    
    # Si responde a un mensaje
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    # Si puso @usuario después del comando
    elif update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'mention':
                target_username = update.message.text[entity.offset:entity.offset+entity.length]
                # Nota: Para mayor precisión, podrías buscar el usuario en contexto, 
                # pero con el nombre directo basta para el mensaje.
                target = target_username
                break

    # 2. Validación de seguridad (si no hay objetivo o si intenta abrazar al bot)
    if not target or (hasattr(target, 'id') and target.id == context.bot.id):
        await update.message.reply_text("¡Aléjate por favor!")
        return

    # 3. Preparar nombre del objetivo
    target_name = target.first_name if hasattr(target, 'first_name') else target
    user = update.effective_user.first_name

    # 4. Frases aleatorias (en inglés como pediste)
    phrases = [
        f"🤗 {user} gave a warm hug to {target_name}!",
        f"✨ {user} wrapped {target_name} in a big, cozy hug.",
        f"💖 {target_name} received a lovely hug from {user}.",
        f"🤗 {user} pulls {target_name} into a tight hug!"
    ]
    
    await update.message.reply_text(random.choice(phrases))

async def kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lógica para obtener el objetivo
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        target = update.message.parse_entities(types=['mention']).get(list(update.message.parse_entities(types=['mention']).keys())[0])

    # Validación: Si no hay objetivo o si es el bot/mismo usuario
    if not target or target.id == context.bot.id:
        await update.message.reply_text("¡Aléjate por favor!")
        return

    # Frases variadas
    phrases = [
        f"{update.message.from_user.first_name} le dio un beso tierno a {target.first_name}.",
        f"{update.message.from_user.first_name} besó apasionadamente a {target.first_name}.",
        f"{target.first_name} recibió un beso lleno de amor de parte de {update.message.from_user.first_name}."
    ]
    await update.message.reply_text(random.choice(phrases))

async def ship(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /ship nombre1 nombre2")
        return
    porcentaje = random.randint(0, 100)
    await update.message.reply_text(f"💘 {context.args[0]} y {context.args[1]} tienen un {porcentaje}% de compatibilidad.")