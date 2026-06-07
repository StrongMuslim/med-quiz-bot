import os
import json
import telebot
from telebot.types import ForceReply

TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = 1050263828

bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'
waiting_feedback = set()

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
        bot.send_message(ADMIN_ID,
            f"🆕 Новый пользователь!\n👤 {name} ({username})\n🆔 {user_id}\n📊 Всего: {len(users)} чел.")
    bot.send_message(message.chat.id,
        "Привет! 👋\n\nЗдесь можно подготовиться к экзамену по "
        "Факультетской терапии — 500 вопросов 🫀\n\n"
        "👇 Нажми кнопку внизу и начинай!\n\nНашёл ошибку? Напиши /feedback")

@bot.message_handler(commands=['feedback'])
def feedback(message):
    waiting_feedback.add(message.from_user.id)
    bot.send_message(message.chat.id,
        "✏️ Напиши своё сообщение — ошибку, пожелание или что угодно. Я передам автору:",
        reply_markup=ForceReply(selective=True))

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 Всего пользователей: {len(users)}")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_feedback and not m.text.startswith('/'))
def receive_feedback(message):
    waiting_feedback.discard(message.from_user.id)
    name = message.from_user.first_name or ''
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"
    bot.send_message(ADMIN_ID,
        f"📩 Новый отзыв!\n👤 {name} ({username})\n🆔 {message.from_user.id}\n\n💬 {message.text}")
    bot.send_message(message.chat.id, "✅ Спасибо! Сообщение отправлено автору.")

bot.infinity_polling()
