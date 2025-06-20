import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import os

# Загрузка .env
load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GPT_MODE = os.getenv("GPT_MODE", "mock")
GOOGLE_SHEET_ENABLED = os.getenv("GOOGLE_SHEET", "false").lower() == "true"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Импорт OpenAI
if GPT_MODE == "real":
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Google Sheets
if GOOGLE_SHEET_ENABLED:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("GPT Bot Leads").sheet1

# Кнопки
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(KeyboardButton("🧴 Услуги"), KeyboardButton("📞 Оставить номер", request_contact=True))
kb.add(KeyboardButton("ℹ️ Контакты"))

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Я ассистент. Чем могу помочь?", reply_markup=kb)

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    name = message.from_user.full_name
    phone = message.contact.phone_number
    await message.answer(f"Спасибо, {name}, мы свяжемся с вами по номеру {phone}!")

    if GOOGLE_SHEET_ENABLED:
        sheet.append_row([name, phone, ""])

@dp.message_handler()
async def handle_text(message: types.Message):
    user_input = message.text

    if GPT_MODE == "mock":
        response = get_mock_response(user_input)
    else:
        response = await get_real_gpt_response(user_input)

    await message.reply(response)

def get_mock_response(user_input):
    if "жирная кожа" in user_input.lower():
        return "Для жирной кожи подойдёт комбинированная чистка лица и маска с глиной. Стоимость 45€."
    elif "подарок" in user_input.lower():
        return "Советую подарочный бокс “Винная палитра”: вино, свеча, краски. 37€, доставка завтра."
    elif "курс" in user_input.lower():
        return "Курс подойдёт новичкам — начнёте с простых форм, на 3 уроке уже будет первая работа."
    elif "услуги" in user_input.lower():
        return "Наши услуги: чистка лица, массаж, пилинги. Напиши, что интересно?"
    elif "контакт" in user_input.lower():
        return "Вы можете написать нам в Instagram: @beauty_shop или позвонить: +7 900 000-00-00"
    else:
        return "Можете уточнить ваш вопрос?"

async def get_real_gpt_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты вежливый ассистент от имени малого бизнеса. Отвечай просто, понятно, доброжелательно."},
            {"role": "user", "content": user_input}
        ]
    )
    return response['choices'][0]['message']['content']
