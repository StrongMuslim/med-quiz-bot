import os
import telebot

TOKEN = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋\n\n"
        "Здесь можно подготовиться к экзамену по "
        "Факультетской терапии — 500 вопросов 🫀\n\n"
        "👇 Нажми кнопку внизу и начинай!"
    )

bot.infinity_polling()
