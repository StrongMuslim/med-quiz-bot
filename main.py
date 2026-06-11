import os
import telebot
from supabase import create_client
from telebot.types import ForceReply, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ['ADMIN_ID'])
AUTHOR_TG = "@eyf1n"

bot = telebot.TeleBot(TOKEN)
db = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

def get_state(user_id):
    r = db.table('user_states').select('state').eq('user_id', user_id).execute()
    return r.data[0]['state'] if r.data else None

def set_state(user_id, state):
    db.table('user_states').upsert({'user_id': user_id, 'state': state}, on_conflict='user_id').execute()

def clear_state(user_id):
    db.table('user_states').delete().eq('user_id', user_id).execute()

def save_reply(message_id, user_id):
    db.table('reply_map').upsert({'message_id': message_id, 'user_id': user_id}, on_conflict='message_id').execute()

def get_reply_user(message_id):
    r = db.table('reply_map').select('user_id').eq('message_id', message_id).execute()
    return r.data[0]['user_id'] if r.data else None

def add_user(user_id, name, username):
    db.table('users').upsert({
        'user_id': user_id, 'name': name, 'username': username
    }, on_conflict='user_id').execute()

def is_new_user(user_id):
    return len(db.table('users').select('user_id').eq('user_id', user_id).execute().data) == 0

def count_users():
    return db.table('users').select('user_id', count='exact').execute().count

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✏️  Нашёл ошибку или проблему", callback_data="feedback"))
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
    save_reply(sent.message_id, user.id)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or ''
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"
    new = is_new_user(user_id)
    add_user(user_id, name, username)
    if new:
        total = count_users()
        bot.send_message(ADMIN_ID,
            f"🆕 Новый пользователь!\n👤 {name} ({username})\n🆔 {user_id}\n📊 Всего: {total} чел.")

    payload = message.text.split()
    if len(payload) > 1 and payload[1] == 'error':
        set_state(user_id, 'feedback')
        bot.send_message(message.chat.id,
            "✏️ Опиши проблему — или прикрепи скриншот.\n\n"
            "Что именно не так: ошибка в вопросе, проблема с сайтом или что-то другое?",
            reply_markup=ForceReply(selective=True))
        return

    bot.send_message(message.chat.id,
        "Привет! 👋\n\n"
        "Здесь можно подготовиться к экзаменам — 400+ вопросов по каждому предмету 🫀\n\n"
        "👇 Нашёл ошибку или есть идея — жми:",
        reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if call.data == "feedback":
        set_state(user_id, 'feedback')
        bot.send_message(chat_id,
            "✏️ Опиши проблему — или прикрепи скриншот.\n\n"
            "Что именно не так: ошибка в вопросе, проблема с сайтом или что-то другое?",
            reply_markup=ForceReply(selective=True))
    elif call.data == "subject":
        set_state(user_id, 'subject')
        bot.send_message(chat_id,
            "📚 Напиши название предмета и курс.\n\n"
            "⚠️ Файл с вопросами обязательно скинь напрямую: @eyf1n\n"
            "Без файла добавить не получится.",
            reply_markup=ForceReply(selective=True))
    elif call.data == "idea":
        set_state(user_id, 'idea')
        bot.send_message(chat_id,
            "💡 Как улучшить сайт?\n\n"
            "Напиши любую идею — новые функции, режимы, удобство.\n"
            "Читаю каждое сообщение 👀",
            reply_markup=ForceReply(selective=True))
    elif call.data == "invite":
        bot.send_message(chat_id,
            "👥 Скинь другу — пусть тоже готовится!\n\n"
            "——————————————\n"
            "Зацени сайт для подготовки к экзаменам — 400+ вопросов по каждому предмету, "
            "учебный режим и экзамен на время. Реально помогает 🫀\n\n"
            "👉 https://strongmuslim.github.io/medfak-quiz\n——————————————")

@bot.message_handler(
    func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message
)
def admin_reply(message):
    target_user = get_reply_user(message.reply_to_message.message_id)
    if not target_user:
        return
    if message.photo:
        bot.send_photo(target_user, message.photo[-1].file_id,
            caption="💬 Ответ автора:\n\n" + (message.caption or ''))
    elif message.document:
        bot.send_document(target_user, message.document.file_id,
            caption="💬 Ответ автора:\n\n" + (message.caption or ''))
    elif message.text:
        bot.send_message(target_user, f"💬 Ответ автора:\n\n{message.text}")
    bot.send_message(ADMIN_ID, "✅ Ответ отправлен пользователю")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        total = count_users()
        bot.send_message(message.chat.id, f"📊 Всего пользователей: {total}")

@bot.message_handler(
    content_types=['text'],
    func=lambda m: m.from_user.id != ADMIN_ID and get_state(m.from_user.id) is not None
    and m.text and not m.text.startswith('/')
)
def receive_text(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    clear_state(user_id)
    if state == 'feedback':
        forward_to_admin("📩 Ошибка/проблема", message.from_user, text=message.text)
        bot.send_message(message.chat.id,
            "✅ Получил, спасибо!\n\n"
            f"Для быстрого ответа можешь написать напрямую: {AUTHOR_TG}")
    elif state == 'subject':
        forward_to_admin("📚 Запрос предмета", message.from_user, text=message.text)
        bot.send_message(message.chat.id,
            "✅ Записал!\n\n"
            f"Теперь скинь файл с вопросами напрямую: {AUTHOR_TG}\n"
            "Без него добавить не смогу 🙏")
    elif state == 'idea':
        forward_to_admin("💡 Идея", message.from_user, text=message.text)
        bot.send_message(message.chat.id, "🔥 Огонь идея! Спасибо, читаю всё 👀")

@bot.message_handler(content_types=['photo'],
    func=lambda m: m.from_user.id != ADMIN_ID and get_state(m.from_user.id) == 'feedback')
def receive_feedback_photo(message):
    clear_state(message.from_user.id)
    forward_to_admin("📸 Скриншот/фото", message.from_user, photo=message.photo[-1].file_id)
    bot.send_message(message.chat.id,
        "✅ Скриншот получен!\n\n"
        f"Для быстрого ответа напиши напрямую: {AUTHOR_TG}")

@bot.message_handler(content_types=['document'],
    func=lambda m: m.from_user.id != ADMIN_ID and get_state(m.from_user.id) == 'feedback')
def receive_feedback_document(message):
    clear_state(message.from_user.id)
    forward_to_admin("📎 Файл", message.from_user, document=message.document.file_id)
    bot.send_message(message.chat.id,
        "✅ Файл получен!\n\n"
        f"Для быстрого ответа напиши напрямую: {AUTHOR_TG}")

bot.infinity_polling()
