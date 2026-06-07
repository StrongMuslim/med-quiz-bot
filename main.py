import os
import json
import telebot
from telebot.types import ForceReply

TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = 1050263828
BOT_LINK = "https://t.me/medfak_kg_bot"

bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'
waiting_feedback = set()
waiting_subject = set()
waiting_idea = set()

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
        "Привет! 👋\n\n"
        "Здесь можно подготовиться к экзамену по "
        "Факультетской терапии — 500 вопросов 🫀\n\n"
        "👇 Нажми кнопку внизу и начинай!\n\n"
        "💡 Есть идеи? /idea\n"
        "👥 Позови друга — /invite")

@bot.message_handler(commands=['feedback'])
def feedback(message):
    waiting_feedback.add(message.from_user.id)
    bot.send_message(message.chat.id,
        "✏️ Напиши об ошибке или пожелании — передам автору:",
        reply_markup=ForceReply(selective=True))

@bot.message_handler(commands=['subject'])
def subject(message):
    waiting_subject.add(message.from_user.id)
    bot.send_message(message.chat.id,
        "📚 Какой предмет хочешь видеть здесь?\n\n"
        "Напиши предмет и курс — например: «Хирургия, 4 курс»\n\n"
        "Стараемся добавлять то, что нужно больше всего 🙏",
        reply_markup=ForceReply(selective=True))

@bot.message_handler(commands=['idea'])
def idea(message):
    waiting_idea.add(message.from_user.id)
    bot.send_message(message.chat.id,
        "💡 Как сделать этот бот лучше?\n\n"
        "Напиши любую идею — новые функции, режимы, удобство. "
        "Читаю каждое сообщение 👀",
        reply_markup=ForceReply(selective=True))

@bot.message_handler(commands=['invite'])
def invite(message):
    bot.send_message(message.chat.id,
        f"👥 Скинь другу — пусть тоже готовится!\n\n"
        f"«Зацени бота для подготовки к экзаменам — 500 вопросов, "
        f"учебный режим и экзамен на время. Реально помогает 🫀»\n\n"
        f"👉 {BOT_LINK}")

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
        f"📩 Отзыв/ошибка!\n👤 {name} ({username})\n\n💬 {message.text}")
    bot.send_message(message.chat.id, "✅ Спасибо! Передал автору.")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_subject and not m.text.startswith('/'))
def receive_subject(message):
    waiting_subject.discard(message.from_user.id)
    name = message.from_user.first_name or ''
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"
    bot.send_message(ADMIN_ID,
        f"📚 Запрос предмета!\n👤 {name} ({username})\n\n{message.text}")
    bot.send_message(message.chat.id, "✅ Записал! Учту при следующем обновлении 🙏")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_idea and not m.text.startswith('/'))
def receive_idea(message):
    waiting_idea.discard(message.from_user.id)
    name = message.from_user.first_name or ''
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"
    bot.send_message(ADMIN_ID,
        f"💡 Идея для развития!\n👤 {name} ({username})\n\n{message.text}")
    bot.send_message(message.chat.id, "✅ Огонь идея! Спасибо, читаю всё 👀")

bot.infinity_polling()
