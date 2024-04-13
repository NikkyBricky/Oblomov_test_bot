# Бунин Николай, 21 группа
# ----------------------------------------------------ИМПОРТЫ-----------------------------------------------------------
import telebot
from telebot.types import ReplyKeyboardMarkup
from dotenv import load_dotenv
import os
import random
import json
import time
from results import find_result
# --------------------------------------------------ПОЛУЧЕНИЕ ТОКЕНА----------------------------------------------------
load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token=token)


# --------------------------------------------------ПРИВЕТСТВИЕ/ПРОЩАНИЕ------------------------------------------------
def check_greet(message):
    greet = ['привет', 'прив', 'приветствую', 'здравствуйте', 'здравствуй', 'йоу', 'hello', 'hi']
    for i in greet:
        if i in message.text.lower():
            return True


def check_bye(message):
    bye = ['пока', 'поки', 'до свидания', 'до встречи', 'бай']
    for i in bye:
        if i in message.text.lower():
            return True


@bot.message_handler(content_types=['text'], func=check_greet)
def greeting(message):
    # одно из привествий связано со временем
    import datetime

    def check_time():
        current_time = datetime.datetime.now().time()
        if current_time < datetime.time(12):
            return f'Доброе утро, {message.from_user.first_name}!'
        elif current_time < datetime.time(18):
            return f'Добрый день, {message.from_user.first_name}!'
        else:
            return f'Добрый вечер, {message.from_user.first_name}!'

    greet_time = check_time()
    bot_greets = ['Привет-привет!', f'Здравствуйте, {message.from_user.first_name}!', 'Приветики-пистолетики!',
                  f'Приветсвую, {message.from_user.first_name}!',
                  f'Здравья желаю, товарищ, {message.from_user.first_name}!', greet_time]
    rand_greet = random.choice(bot_greets)
    bot.send_message(message.chat.id, rand_greet)


@bot.message_handler(content_types=['text'], func=check_bye)
def farewell(message):
    bye = (f'До встречи, {message.from_user.first_name}! Если захотите еще раз услышать об интересных людях, '
           f'я всегда к вашим услугам.')
    bot.send_message(message.chat.id, bye)


# -----------------------------------------------------JSON-------------------------------------------------------------
with open('Oblomov_test_bot/my_questionnaire.json', 'r', encoding='utf8') as file:
    questionnaire = json.load(file)


def save_to_json():
    with open('Oblomov_test_bot/user_data.json', 'w', encoding='utf8') as f:
        json.dump(user_data, f, indent=2)


def load_from_json():
    # noinspection PyBroadException
    try:
        with open('Oblomov_test_bot/user_data.json', 'r+', encoding='utf8') as f:
            data = json.load(f)
    except Exception:
        data = {}

    return data


user_data = load_from_json()


# ------------------------------------------------------ЗАПУСК БОТА-----------------------------------------------------
@bot.message_handler(commands=['start'])
def starting(message):
    load_from_json()
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(2)
    bot.send_chat_action(message.chat.id, action='upload_photo')
    time.sleep(2)
    keyboard = check_main_menu_keyboard(message)
    greet = 'Привет! Я бот, который умеет определять, кто ты из романа И. А. Гончарова "Обломов". Начнем?'
    pic = 'https://i.postimg.cc/g2m0Ngj7/book.jpg'
    bot.send_photo(message.chat.id, pic, greet, reply_markup=keyboard)
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {'result': False}
        save_to_json()


# ---------------------------------------------НАЧАЛО ТЕСТИРОВАНИЯ------------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message:  'начать тестирование' in message.text.lower() or
                     'начать сначала' in message.text.lower())
def start_test(message):
    load_from_json()
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(1.5)
    user_id = str(message.from_user.id)
    if user_id not in user_data:  # на случай, если файл с данными пользователей удален.
        user_data[user_id] = {}
        save_to_json()
    try:
        test_is_on = user_data[user_id]['test_is_on']
        if not test_is_on:
            make_params_to_start(message)
        else:
            bot.send_message(message.chat.id, 'Пожалуйста, вернитесь в главное меню, если хотите начать сначала.')
            return
    except KeyError:
        make_params_to_start(message)

    keyboard = check_answers_keyboard(message)
    question_number = user_data[user_id]['question_number']
    question = questionnaire[str(question_number)]['question']
    bot.send_message(message.chat.id, f'Вопрос №{question_number}\n\n {question}',
                     reply_markup=keyboard)


def check_user(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        bot.send_message(user_id, 'Кажется, ввиду технических работ, я удалил ваши данные.')
        bot.send_message(user_id, 'Запускаю тестирование заново...')
        time.sleep(2)
        return False
    return True


def make_params_to_start(message):  # так как параметров вышло много, решил перенести их в отдельную функцию
    load_from_json()
    user_id = str(message.from_user.id)
    user_data[user_id] = {'question_number': 1,
                          'values': {'oblomov': 0, 'shtolz': 0, 'olga': 0, 'zakhar': 0},
                          'test_is_on': True,
                          'result': False,
                          'answers': {}}
    save_to_json()


# -----------------------------------------------ЛОГИКА ТЕСТИРОВАНИЯ----------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message: message.text.isdigit())
def test(message):
    load_from_json()
    user_id = str(message.from_user.id)
    user = check_user(message)
    if not user:
        start_test(message)
        return
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(1.5)
    question_number = user_data[user_id]['question_number']
    answers = []
    for key in questionnaire[str(question_number)].keys():  # сделано для авто-нахождения возможных вариантов ответа
        if 'value' in key:
            answers.append(key[5])
    if user_data[user_id]['test_is_on']:
        if message.text.lower() not in answers:
            bot.send_message(message.chat.id, 'Нет такого ответа. Попробуй снова.')
        else:

            ans = message.text  # получаем ответ на вопрос
            user_data[user_id]['answers'][f'quest{question_number}'] = ans  # сохраняем ответ
            value = questionnaire[str(question_number)][f'value{ans}']  # получаем значение ответа
            user_data[user_id]['values'][value] += 1  # прибавляем балл к шкале соответствующей полученному значению
            save_to_json()
            question_number += 1  # переходим к следующему вопросу
            if question_number <= len(questionnaire.keys()):
                user_data[user_id]['question_number'] = question_number
                keyboard = check_answers_keyboard(message)
                question = questionnaire[str(question_number)]['question']
                bot.send_message(message.chat.id, f'Вопрос №{question_number}\n\n {question}',
                                 reply_markup=keyboard)
                save_to_json()
            else:

                user_data[user_id]['test_is_on'] = False
                user_data[user_id]['result'] = True
                save_to_json()
                say_result(message)
    else:
        bot.send_message(message.chat.id, 'Я пока не знаю, как работать с такой формулировкой сообщения.\n'
                                          'Если хотите пройти мой тест, то смело жмите на кнопку '
                                          '"Начать тестирование" или, если Вы уже проходили этот тест ранее, '
                                          'нажмите "Начать сначала"')


@bot.message_handler(content_types=['text'], func=lambda message: 'вернуться в главное меню' in message.text.lower())
def back_to_main_menu(message):
    load_from_json()
    user = check_user(message)
    if not user:
        start_test(message)
        return
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(1)
    user_id = str(message.from_user.id)
    keyboard = check_main_menu_keyboard(message)
    bot.send_message(message.chat.id, 'Что вам угодно?', reply_markup=keyboard)
    user_data[user_id]['test_is_on'] = False
    save_to_json()


@bot.message_handler(content_types=['text'], func=lambda message: 'предыдущий вопрос' in message.text.lower())
def question_before(message):
    load_from_json()
    user_id = str(message.from_user.id)
    user = check_user(message)
    if not user:
        start_test(message)
        return
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(1.5)
    question_number = user_data[user_id]['question_number']
    if user_data[user_id]['test_is_on']:
        if question_number != 1:
            question_number -= 1  # переходим к предыдущему вопросу
            user_data[user_id]['question_number'] = question_number
            ans = user_data[user_id]['answers'][f'quest{question_number}']  # находим ответ на предыдущий вопрос
            value = questionnaire[str(question_number)][f'value{ans}']  # находим значение этого ответа
            user_data[user_id]['values'][value] -= 1  # удаляем это значение

            keyboard = check_answers_keyboard(message)
            question = questionnaire[str(question_number)]['question']
            bot.send_message(message.chat.id, f'Вопрос №{question_number}\n\n {question}',
                             reply_markup=keyboard)
            save_to_json()
        else:
            bot.send_message(message.chat.id, 'Нельзя вернуться к предыдущему вопросу, так как это первый вопрос.')


@bot.message_handler(content_types=['text'], func=lambda message: 'продолжить' in message.text.lower())
def carry_on(message):
    load_from_json()
    user = check_user(message)
    if not user:
        start_test(message)
        return
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(1.5)
    user_id = str(message.from_user.id)
    question_number = user_data[user_id]['question_number']
    user_data[user_id]['test_is_on'] = True
    keyboard = check_answers_keyboard(message)
    question = questionnaire[str(question_number)]['question']
    bot.send_message(message.chat.id, f'Вопрос №{question_number}\n\n {question}',
                     reply_markup=keyboard)
    save_to_json()


# ------------------------------------------------ВЫВОД РЕЗУЛЬТАТА------------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message: 'мой результат' in message.text.lower())
def say_result(message):
    load_from_json()
    user_id = str(message.from_user.id)
    user = check_user(message)
    if not user:
        start_test(message)
        return
    if user_data[user_id]['result']:
        bot.send_chat_action(message.chat.id, action='typing')
        time.sleep(3)
        bot.send_chat_action(message.chat.id, action='upload_photo')
        time.sleep(2)
        result = []
        values = user_data[user_id]['values']
        max_value = max(values.values())
        for key, value in user_data[user_id]['values'].items():
            if value == max_value:
                result.append(key)
        if len(result) == 1:
            pic, text = find_result(user_data, user_id, result)
            bot.send_photo(user_id, pic, text, reply_markup=None)
        else:
            text = find_result(user_data, user_id, result)
            bot.send_message(user_id, text, reply_markup=check_main_menu_keyboard(message))
    else:
        bot.send_message(message.chat.id, 'Вы еще не закончили тестирование, '
                                          'поэтому ваших результатов у меня пока нет.')


@bot.message_handler(content_types=['text', 'voice', 'photo', 'audio'])
def answer_to_all(message):
    bot.send_chat_action(message.chat.id, action='typing')
    time.sleep(1.5)
    bot.send_message(message.chat.id, 'Я пока не знаю, как работать с такой формулировкой сообщения.\n'
                                      'Если хотите пройти мой тест, то смело жмите на кнопку "Начать тестирование" или,'
                                      ' если Вы уже проходили этот тест ранее, нажмите "Начать сначала"')


# --------------------------------------------------КЛАВИАТУРЫ----------------------------------------------------------
def check_answers_keyboard(message):
    user_id = str(message.from_user.id)
    if user_data[user_id]['question_number'] == 1:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4).add('1', '2', '3', '4',
                                                                            'Вернуться в главное меню')
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4).add('1', '2', '3', '4',
                                                                            'Вернуться в главное меню',
                                                                            'Предыдущий вопрос')
    return markup


def check_main_menu_keyboard(message):
    load_from_json()
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        markup = ReplyKeyboardMarkup(resize_keyboard=True).add('Начать тестирование')
    elif user_data[user_id]['result']:
        markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add('Начать сначала',
                                                                            'Мой результат')
    else:
        markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add('Начать сначала', 'Продолжить')
    return markup


bot.infinity_polling()  # запуск бота
