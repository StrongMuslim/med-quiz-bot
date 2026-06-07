import os
import json
import telebot

TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = 1050263828

bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users), f)

users = load_users()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    is_new = user_id not in users

    if is_new:
        users.add(user_id)
        save_users(users)
        name = message.from_user.first_name or ''
        username = f"@{message.from_user.username}" if message.from_user.username else "без username"
        bot.send_message(
            ADMIN_ID,
            f"🆕 Новый пользователь!\n"
            f"👤 {name} ({username})\n"
            f"🆔 {user_id}\n"
            f"📊 Всего: {len(users)} чел."
        )

    bot.send_message(
        message.chat.id,
        "Привет! 👋\n\n"
        "Здесь можно подготовиться к экзамену по "
        "Факультетской терапии — 500 вопросов 🫀\n\n"
        "👇 Нажми кнопку внизу и начинай!"
    )

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            f"📊 Статистика бота:\n👥 Всего пользователей: {len(users)}"
        )

bot.infinity_polling()
