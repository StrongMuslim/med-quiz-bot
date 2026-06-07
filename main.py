import os
import json
import telebot
from telebot.types import ForceReply, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = 1050263828
BOT_LINK = "https://t.me/medfak_kg_bot"

bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'
waiting_feedback = set()
waiting_subject = set()
waiting_idea = set()
reply_map = {}

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

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✏️  Нашёл ошибку", callback_data="feedback"))
    markup.add(InlineKeyboardButton("📚  Хочу другой предмет", callback_data="subject"))
    markup.add(InlineKeyboardButton("💡  Есть идея для развития", callback_data="idea"))
    markup.add(InlineKeyboardButton("👥  Позвать друга", callback_data="invite"))
    return markup

def forward_to_admin(label, user, text=None, photo=None, document=None):
    name = user.first_name or ''
    username = f"@{user.username}" if user.username else "без username"
    caption = f"{label}\n👤 {name} ({username})\n🆔 {user.id}"
    if text:
        sent = bot.send_message(ADMIN_ID, f"{caption}\n\n{text}")
    elif photo:
        sent = bot.send_photo(ADMIN_ID, photo, caption=caption)
    elif document:
        sent = bot.send_document(ADMIN_ID, document, caption=caption)
    else:
        return
    reply_map[sent.message_id] = user.id

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
            f"Новый пользователь!\nИмя: {name} ({username})\nID: {user_id}\nВсего: {len(users)} чел.")
    bot.send_message(message.chat.id,
        "Привет! 👋\n\n"
        "Здесь можно подготовиться к экзамену по "
        "Факультетской терапии — 500 вопросов 🫀\n\n"
        "👇 Нажми кнопку внизу и начинай!",
        reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if call.data == "feedback":
        waiting_feedback.add(user_id)
        bot.send_message(chat_id, "✏️ Напиши об ошибке — или прикрепи скриншот/файл:",
            reply_markup=ForceReply(selective=True))
    elif call.data == "subject":
        waiting_subject.add(user_id)
        bot.send_message(chat_id,
            "📚 Какой предмет и курс хочешь видеть здесь?\n\nНапример: Хирургия, 4 курс\n\nСтараемся добавлять то, что нужно больше всего 🙏",
            reply_markup=ForceReply(selective=True))
    elif call.data == "idea":
        waiting_idea.add(user_id)
        bot.send_message(chat_id,
            "💡 Как улучшить бот?\n\nНапиши любую идею — новые функции, режимы, удобство.\nЧитаю каждое сообщение 👀",
            reply_markup=ForceReply(selective=True))
    elif call.data == "invite":
        bot.send_message(chat_id,
            f"👥 Скинь другу — пусть тоже готовится!\n\n——————————————\nЗацени бота для подготовки к экзаменам — 500 вопросов, учебный режим и экзамен на время. Реально помогает 🫀\n\n👉 {BOT_LINK}\n——————————————")

@bot.message_handler(
    func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message and m.reply_to_message.message_id in reply_map
)
def admin_reply(message):
    target_user = reply_map.get(message.reply_to_message.message_id)
    if not target_user:
        return
    if message.photo:
        bot.send_photo(target_user, message.photo[-1].file_id, caption="💬 Ответ автора:\n\n" + (message.caption or ''))
    elif message.document:
        bot.send_document(target_user, message.document.file_id, caption="💬 Ответ автора:\n\n" + (message.caption or ''))
    elif message.text:
        bot.send_message(target_user, f"💬 Ответ автора:\n\n{message.text}")
    bot.send_message(ADMIN_ID, "✅ Ответ отправлен пользователю")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 Всего пользователей: {len(users)}")

@bot.message_handler(
    func=lambda m: m.from_user.id != ADMIN_ID and (
        m.from_user.id in waiting_feedback or
        m.from_user.id in waiting_subject or
        m.from_user.id in waiting_idea
    ) and not m.text.startswith('/')
)
def receive_text(message):
    user_id = message.from_user.id
    if user_id in waiting_feedback:
        waiting_feedback.discard(user_id)
        forward_to_admin("📩 Ошибка/отзыв", message.from_user, text=message.text)
        bot.send_message(message.chat.id, "✅ Спасибо! Передал автору.")
    elif user_id in waiting_subject:
        waiting_subject.discard(user_id)
        forward_to_admin("📚 Запрос предмета", message.from_user, text=message.text)
        bot.send_message(message.chat.id, "✅ Записал! Учту при следующем обновлении 🙏")
    elif user_id in waiting_idea:
        waiting_idea.discard(user_id)
        forward_to_admin("💡 Идея", message.from_user, text=message.text)
        bot.send_message(message.chat.id, "🔥 Огонь идея! Спасибо, читаю всё 👀")

@bot.message_handler(content_types=['photo'],
    func=lambda m: m.from_user.id != ADMIN_ID and m.from_user.id in waiting_feedback)
def receive_photo(message):
    waiting_feedback.discard(message.from_user.id)
    forward_to_admin("📸 Фото/скриншот", message.from_user, photo=message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ Фото получено! Передал автору.")

@bot.message_handler(content_types=['document'],
    func=lambda m: m.from_user.id != ADMIN_ID and m.from_user.id in waiting_feedback)
def receive_document(message):
    waiting_feedback.discard(message.from_user.id)
    forward_to_admin("📎 Файл", message.from_user, document=message.document.file_id)
    bot.send_message(message.chat.id, "✅ Файл получен! Передал автору.")

bot.infinity_polling()
