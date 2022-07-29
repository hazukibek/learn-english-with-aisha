import os
import telebot
import logging
import psycopg2
from config import *
from flask import Flask, request
from telebot import types

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)


db_connection = psycopg2.connect(DB_URI, sslmode='require')
db_object = db_connection.cursor()


def update_messages_count(user_id):
    db_object.execute(f"UPDATE users SET messages = messages + 1 WHERE id = {user_id}")
    db_connection.commit()


@bot.message_handler(commands=['start'])
def start(message):
    global user_id
    user_id = message.from_user.id
    username = message.from_user.username
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    yes = types.KeyboardButton("Хорошо")
    markup.add(yes)
    bot.reply_to(message, f'Добро пожаловать, {username}. Перед работой с данным ботом, Вы должны ответить на несколько вопросов.', reply_markup=markup)

    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, messages) VALUES (%s, %s, %s)", (user_id, username, 0))
        db_connection.commit()

    update_messages_count(user_id)


@bot.message_handler(content_types=['text'])
def reg(message):
    markup_close = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Предлагаю познакомиться! Как вас зовут?", reply_markup=markup_close)
    bot.register_next_step_handler(message, reg_name)


def reg_name(message):
    global name
    name = message.text
    bot.reply_to(message, "Прекрасное имя!")
    bot.send_message(message.chat.id, "Сколько Вам лет?")
    bot.register_next_step_handler(message, reg_age)


def reg_age(message):
    global age
    age = int(message.text)
    bot.reply_to(message, "Окей")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button1 = types.KeyboardButton("Женский")
    button2 = types.KeyboardButton("Мужской")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Ваш пол:", reply_markup=markup)
    bot.register_next_step_handler(message, reg_sex)


def reg_sex(message):
    global sex
    sex = message.text
    global f
    if sex == "Женский":
        f = -161
    else:
        f = 5
    bot.send_message(message.chat.id, "Ваш рост в сантиметрах?", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, reg_height)


def reg_height(message):
    global height
    height = int(message.text)
    bot.send_message(message.chat.id, "Сколько Вы весите в киллограммах?")
    bot.register_next_step_handler(message, reg_weight)


def reg_weight(message):
    global weight
    weight = int(message.text)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button1 = types.KeyboardButton("Минимальная активность")
    button2 = types.KeyboardButton("Слабая активность: раз в неделю")
    button3 = types.KeyboardButton("Средняя активность: 3 раза в неделю")
    button4 = types.KeyboardButton("Высокая активность: почти каждый день")
    button5 = types.KeyboardButton("Экстра-активность: тяжелая физическая работа; спорт")
    markup.add(button1, button2, button3, button4, button5)
    bot.send_message(message.chat.id, "Ваша степень физической активности:", reply_markup=markup)
    bot.register_next_step_handler(message, reg_phy)


def reg_phy(message):
    global phy
    phy = message.text
    bot.reply_to(message, 'Cпасибо за информацию!', reply_markup=types.ReplyKeyboardRemove())
    if phy == "Минимальная активность":
        A = 1.2
    elif phy == "Слабая активность: раз в неделю":
        A = 1.375
    elif phy == "Средняя активность: 3 раза в неделю":
        A = 1.55
    elif phy == "Высокая активность: почти каждый день":
        A = 1.725
    elif phy == "Экстра-активность: тяжелая физическая работа; спорт":
        A = 1.9
    else:
        bot.send_message(message.chat.id, "invalid data")
    call = (10 * weight + 6.25 * height - 5 * age + f) * A
    bot.send_message(message.chat.id,  "Бот расчитывает количество калорий по формуле Миффлина-Сан Жеора- одной из самых последних формул расчета калорий для оптимального похудения или сохранения нормального веса.")
    bot.send_message(message.chat.id, "Необходимое количество килокалорий (ккал) в сутки для Вас = " + str(call)+" "+"ккал")
    bot.send_message(message.chat.id, "Хотите узнать ")
    db_object.execute("INSERT INTO users(age, height, weight, call, name, phy, sex) VALUES (%s, %s, %s, %s, %s, %s, %s)",(age, height, weight, call, name, phy, sex))
    db_connection.commit()


@bot.message_handler(commands=['receipt'])
def buttons(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    receipt = types.KeyboardButton("Рецепты")
    data = types.KeyboardButton("Моя персональная информация")
    info = types.KeyboardButton("О боте")
    exit = types.KeyboardButton("Выход")
    markup.add(receipt, data)
    markup.add(info, exit)
    bot.send_message(message.chat.id, 'Выберите действие на меню', reply_markup=markup)


@bot.message_handler(commands=['data'])
def user_text(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button1 = types.KeyboardButton(text='Имя')
    button2 = types.KeyboardButton(text='Возраст')
    button3 = types.KeyboardButton(text='Пол')
    button4 = types.KeyboardButton(text='Рост')
    button5 = types.KeyboardButton(text='Вес')
    button6 = types.KeyboardButton(text='Физическая активность')
    button7 = types.KeyboardButton(text='Ккал в сутки')
    button8 = types.KeyboardButton(text='Назад')
    markup.row(button1, button2, button3, button4)
    markup.row(button5, button6, button7, button8)
    bot.send_message(message.chat.id, '', reply_markup=markup)


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, 'Этот бот аспротльдб')


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
