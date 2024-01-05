# ----------------------------------------------------ИМПОРТЫ-----------------------------------------------------------
import telebot
from telebot.types import ReplyKeyboardMarkup
from dotenv import load_dotenv
import os
import random
import json

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
with open('my_questionnaire.json', 'r', encoding='utf8') as file:
    questionnaire = json.load(file)


def save_to_json():
    with open('user_data.json', 'w', encoding='utf8') as f:
        json.dump(user_data, f, indent=2)


def load_from_json():
    try:
        with open('user_data.json', 'r+', encoding='utf8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    return data


user_data = load_from_json()


# ------------------------------------------------------ЗАПУСК БОТА-----------------------------------------------------
@bot.message_handler(commands=['start'])
def starting(message):
    load_from_json()
    keyboard = check_main_menu_keyboard(message)
    greet = 'Привет! Я бот, который умеет определять, кто ты из романа И. А. Гончарова "Обломов". Начнем?'
    bot.send_message(message.chat.id, greet, reply_markup=keyboard)
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {}
        save_to_json()


# ---------------------------------------------НАЧАЛО ТЕСТИРОВАНИЯ------------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message:  'начать тестирование' in message.text.lower() or
                     'начать сначала' in message.text.lower())
def start_test(message):
    load_from_json()
    user_id = str(message.from_user.id)
    try:
        if not user_data[user_id]['test_is_on']:
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


def make_params_to_start(message):  # так как параметров вышло много, решил перенести их в отдельную функцию
    load_from_json()
    user_id = str(message.from_user.id)
    user_data[user_id]['question_number'] = 1
    user_data[user_id]['values'] = {}
    user_data[user_id]['values']['oblomov'] = 0
    user_data[user_id]['values']['shtolz'] = 0
    user_data[user_id]['values']['olga'] = 0
    user_data[user_id]['values']['zakhar'] = 0
    user_data[user_id]['test_is_on'] = True
    user_data[user_id]['result'] = False
    user_data[user_id]['answers'] = {}
    save_to_json()


# -----------------------------------------------ЛОГИКА ТЕСТИРОВАНИЯ----------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message: message.text.isdigit())
def test(message):
    load_from_json()
    user_id = str(message.from_user.id)
    question_number = user_data[user_id]['question_number']
    answers = []
    for key in questionnaire[str(question_number)].keys():
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
                to_result(message)
    else:
        bot.send_message(message.chat.id, 'Я пока не знаю, как работать с такой формулировкой сообщения.\n'
                                          'Если хотите пройти мой тест, то смело жмите на кнопку '
                                          '"Начать тестирование" или, если Вы уже проходили этот тест ранее, '
                                          'нажмите "Начать сначала"')


@bot.message_handler(content_types=['text'], func=lambda message: 'вернуться в главное меню' in message.text.lower())
def back_to_main_menu(message):
    load_from_json()
    user_id = str(message.from_user.id)
    keyboard = check_main_menu_keyboard(message)
    bot.send_message(message.chat.id, 'Что вам угодно?', reply_markup=keyboard)
    user_data[user_id]['test_is_on'] = False
    save_to_json()


@bot.message_handler(content_types=['text'], func=lambda message: 'предыдущий вопрос' in message.text.lower())
def question_before(message):
    load_from_json()
    user_id = str(message.from_user.id)
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
    user_id = str(message.from_user.id)
    question_number = user_data[user_id]['question_number']
    user_data[user_id]['test_is_on'] = True
    keyboard = check_answers_keyboard(message)
    bot.send_message(message.chat.id, questionnaire[str(question_number)]['question'],
                     reply_markup=keyboard)
    save_to_json()


# ------------------------------------------------ВЫВОД РЕЗУЛЬТАТА------------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message: 'мой результат' in message.text.lower())
def to_result(message):
    load_from_json()
    user_id = str(message.from_user.id)
    if user_data[user_id]['result']:
        save_to_json()
        result = []
        max_value = max(user_data[user_id]['values']['oblomov'], user_data[user_id]['values']['shtolz'],
                        user_data[user_id]['values']['olga'], user_data[user_id]['values']['zakhar'])
        for key, value in user_data[user_id]['values'].items():
            if value == max_value:
                result.append(key)
        if len(result) == 1:
            percent = int(user_data[user_id]['values'][f'{result[0]}'] / 9 * 100)
            if 'oblomov' in result:
                bot.send_message(message.chat.id, 'Вы - Илья Ильич Обломов на '
                                 f'{percent}%.\n'
                                 ' Раз Вам выпал такой результат, значит слова о том,'
                                 ' что литературные герои вечны, действительно верны.'
                                 ' Вы ленивец и бездельник. Ваша жизнь состоит из однообразных, '
                                 'повторяющихся событий, она стоит на месте.'
                                 ' Вы склонны к бездействию и принятию самого легкого пути. '
                                 'Для Вас наверняка является частым явление откладывания дел на потом.'
                                 ' Вы не умеете проявлять инициативу'
                                 ' и не способны к преодолению трудностей. Но это не повод сдаваться.'
                                 ' В жизни редко бывает второй шанс,'
                                 ' ведь часто мы осознаем свои проблемы слишком поздно.'
                                 ' Однако, надеюсь, сейчас, прочитав свой результат Вы поймете, '
                                 'что нужно начать меняться.'
                                 ' Жизни нужно движение, человеку необходимо постоянно двигаться'
                                 ' вперед, иначе род наш переведется. Поэтому дерзайте! Желаю удачи!',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'shtolz' in result:
                bot.send_message(message.chat.id, 'Вы - Андрей Иванович Штольц на \n'
                                                  f'{percent}%.\n'
                                                  'Бытует много разных мнений насчет того, '
                                                  'хороши ли характеристики этого персонажа или нет. '
                                                  'Выбор я оставлю за Вами.\n'
                                                  'Итак, Вы уверенно смотрите вперёд. Вам чужды эфемерные фантазии, Вы '
                                                  'с энтузиазмом достигаете поставленных целей, упорно трудитесь. '
                                                  'Вы деятельны, не боитесь браться за новую работу, '
                                                  'развивать себя в новой сфере. Но кто знает, '
                                                  'к чему приведет постоянный труд? Никто не знает, что будет в конце. '
                                                  'Вечное счастье или мука.'
                                                  ' Может, во втором случае, лучше быть Обломовым?\n'
                                                  'Вы любите своих близких, вам нравится помогать им и заботиться о них'
                                                  '. Иногда бываете немного педантичны, '
                                                  'любите, когда все под контролем, все точно и аккуратно сделано.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'olga' in result:
                bot.send_message(message.chat.id, 'Вы - Ольга Сергеевна Ильинская на '
                                                  f'{percent}%.\n'
                                                  'Говорят, что красота требует жертв. Говоря об Ольге, '
                                                  'сложно с этим не согласиться, ведь она сирота, '
                                                  'так еще и довелось ей встречаться с Обломовым. Но сейчас не об этом.'
                                                  'Вы эмоциональный и чувствительный человек. '
                                                  'Вами движут тверждые убеждения. Ваша жизнь основана '
                                                  'на постоянном движении вперед,'
                                                  ' на желании знать как можно больше об этом прекрасном мире. '
                                                  'Вы прогрессивны, решительны, умны и образованны.'
                                                  ' Но несмотря на все эти положительны моменты, '
                                                  'Вы бываете непостоянны, иногда Вас сложно понять. Также Вам присущ,'
                                                  'хоть и проявляется редко, так называемый синдром спасателя. Иногда'
                                                  'Вам кажется, что без Вас не справятся, дело не пойдет, хотя Ваша'
                                                  'помощь в нем вовсе не требуется. ',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'zakhar' in result:
                bot.send_message(message.chat.id, 'Вы - Захар на '
                                                  f'{percent}%.\n'
                                                  'Что-ж, интересный у Вас результат. Сейчас расскажу по подробнее.\n'
                                                  'Ваше самое главное качество - это преданность. '
                                                  'Если человек заслужил ваше доверие, '
                                                  'то Вы будете готовы потакать ему в чем угодно. Однако трудолюбием Вы'
                                                  'не одарены. Поэтому большую часть своего свободного времени Вы'
                                                  ' проводите за развлечениями. Но как же без труда'
                                                  ' получить возможность для этого? Отсюда вытекает '
                                                  'Ваша хитрость и коварство. Вы ловко распоряжаетесь своим положением '
                                                  'и стараетесь извлекать из него максимальную выгоду.'
                                                  'Принимать ошибки у Вас плохо получается. Зачастую по вашему мнению в'
                                                  'них виноваты не Вы, а кто-нибудь другой, на кого Вы непременно '
                                                  'начинаете перекладывать за них ответственность.',
                                 reply_markup=check_main_menu_keyboard(message))
        elif len(result) == 2:
            percent = int(user_data[user_id]['values'][f'{result[0]}']/9 * 100) * 2
            if 'oblomov' in result and 'shtolz' in result:
                bot.send_message(message.chat.id, f'Вы Обломов и Штольц на {percent}%\n'
                                 'Вы имеете одинаковое количество очков у двух антиподов. '
                                 'Такого быть не должно. '
                                 'Скорее всего Вы где-то солгали. Перепройдите тест, '
                                 'ответьте честно и узрите свой результат.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'oblomov' in result and 'olga' in result:
                bot.send_message(message.chat.id, f'Вы Обломов и Ольга на {percent}%\n'
                                 'Вы умны и образованны, у Вас прекрасные мечты и грандиозные цели. '
                                 'Однако Вам также присущи лень и безответственность, '
                                 'что мешает Вам в достижении этих целей. Ваш характер двояк: '
                                 'в один момент Вы считаете себя "жертвой" и ждете,'
                                 ' пока Вам кто-нибудь поможет, а в другой - '
                                 'становитесь "спасателем" и начинаете всем помогать, но, так как'
                                 ' Вы отчасти лежебока, то помощь Ваша заключается '
                                 'лишь в самых простых действиях, поэтому окружающие иногда даже не замечают ее.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'oblomov' in result and 'zakhar' in result:
                bot.send_message(message.chat.id, f'Вы Обломов и Захар на {percent}%\n'
                                 'Что-ж, Ваш результат - самая худшая связка в данном тесте.'
                                 ' Вы ленивец и бездельник. Ваша жизнь состоит из однообразных, '
                                 'повторяющихся событий, она стоит на месте.'
                                 ' Вы склонны к бездействию и принятию самого легкого пути. '
                                 'Больше всего  Вам нравится развлекаться и ничего не делать. Вы умны,'
                                 ' но используете свой разум не во благо. '
                                 'Вам не нравится принимать свои ошибки,'
                                 ' поэтому ответственность за них Вы часто перекладываете на других. '
                                 'Скорее всего в Вашей жизни сейчас застой, поэтому советую Вам начать'
                                 ' двигаться по жизни, развиваться, добиваться результатов,'
                                 ' иначе цветок Вашей жизни попросту завянет в пучине бездействия.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'shtolz' in result and 'olga' in result:
                bot.send_message(message.chat.id, f'Вы Штольц и Ольга на {percent}%\n'
                                 'Поздравляю! Кажется, Вы смогли достигнуть гармонии в своей жизни, '
                                 'ведь вы уверенно смотрите вперёд, с энтузиазмом достигаете '
                                 'поставленных целей, упорно трудитесь. Зачастую Ваш труд '
                                 'направлен на помощь другим. Вы чувствительны'
                                 ' и заботливы, особенно по отношению к родным и близким. Вы творческий'
                                 ' человек, Вам нравится постоянно учиться чему-то новому,'
                                 'пробовать себя в новой сфере. Иногда Вам бывает трудно '
                                 'справиться со своими переживаниями, но у Вас всегда есть тот, кто '
                                 'сможет дать Вам дельный совет. ',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'shtolz' in result and 'zakhar' in result:
                bot.send_message(message.chat.id, f'Вы Штольц и Захар на {percent}%\n'
                                 'Вы деятельны, не боитесь никаких преград, для Вас труд - один '
                                 'из главных двигателей в жизни. На первый взгляд, в Вас много энергии'
                                 ', но если присмотреться поближе, то каждый раз достигая своих целей,'
                                 ' вы как бы находитесь на грани истощения, во время работы Вам'
                                 ' очень часто хочется бросить все на неопределенный срок'
                                 ', отвлечься, просто лечь и ничего не делать. Так как Вы амбициозны, '
                                 'то Вам присущи грандиозные цели и, конечно, множество ошибок на пути'
                                 ' к ним. С ними Вы стараетесь справляться, но иногда не выдерживаете,'
                                 ' и пытаетесь перебросить вину за них на другого человека, обвинить'
                                 ' его во всех своих бедах. Вы понимаете, что это нехорошо, но'
                                 ' не можете с собой ничего поделать.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'olga' in result and 'zakhar' in result:
                bot.send_message(message.chat.id, f'Вы Ольга и Захар на {percent}%\n'
                                 'Вы очень эмоциональный человек, переживаете по любому поводу. '
                                 'Ваше беспокойство не ограничивается Вами. Вы очень заботливы и '
                                 'сострадательны. Ваша жизнь по большей мере состоит как раз из'
                                 ' помощи другим людям. Но помогаете Вы не всем, а только тем, кто'
                                 ' заслужил ваше доверие. Вы готовы на все ради таких людей. Вам '
                                 'очень тяжело принимать свои промахи. Очень часто Вы умалчиваете'
                                 ' о них, долго думаете, что бы было, если бы Вы их не совершали.',
                                 reply_markup=check_main_menu_keyboard(message))
        else:
            percent = int(user_data[user_id]['values'][f'{result[0]}'] / 9 * 100) * 3
            if 'oblomov' in result and 'zakhar' in result and 'olga' in result:
                bot.send_message(message.chat.id, 'Вы схожи одновременно с Ильей Обломовым, Захаром и Ольгой на '
                                                  f'{percent}%\n'
                                                  'Вы довольно противоречивая личность. '
                                                  'С одной стороны Вы бываете очень ленивы и безответственны, '
                                                  'зачастую Вам очень сложно достигать поставленных целей. Однако, с'
                                                  'другой стороны, Вам очень нравится получать знания, изучать что-либо'
                                                  ', учиться чему-то новому. Без этого Вам бывает тяжело, но обычно'
                                                  'Вы чувствуете себя комфортно в простом пребывании дома, лежа на'
                                                  'диване или кровати.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'oblomov' in result and 'zakhar' in result and 'shtolz' in result:
                bot.send_message(message.chat.id, 'Вы схожи одновременно с Ильей Обломовым, Захаром и Штольцем на '
                                                  f'{percent}%\n'
                                                  'Ваши самые хорошие качества, которые на самом деле проявляются не'
                                                  'так часто - это преданность и трудолюбие. Но зачастую Ваша'
                                                  ' преданность граничит с ложью и коварством, а трудолюбие - с'
                                                  'желанием все бросить и надолго залезть в пучину бездействия.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'oblomov' in result and 'shtolz' in result and 'olga' in result:
                bot.send_message(message.chat.id, 'Вы схожи одновременно с Ильей Обломовым, Штольцем и Ольгой на '
                                                  f'{percent}%\n'
                                                  'Вы хороши в помощи другим людям, '
                                                  'Вам даже нравится трудиться ради кого-то.'
                                                  ' Вы всегда готовы прийти на помощь,'
                                                  ' но люди Вас почему-то не сильно то и ценят. Дело в том,'
                                                  ' что Вы из себя мало что представляете: Вы вроде бы есть,'
                                                  ' а вроде бы и нет. Ваша жизнь аморфна.'
                                                  ' Вас часто можно спутать с ветерком, '
                                                  'который подует, иногда его почувствуют , '
                                                  'но довольно скоро совсем позабудут о нём.',
                                 reply_markup=check_main_menu_keyboard(message))
            if 'zakhar' in result and 'shtolz' in result and 'olga' in result:
                bot.send_message(message.chat.id, 'Вы схожи одновременно с Андреем Штольцем, Захаром и Ольгой на '
                                                  f'{percent}%\n'
                                                  'Вам нравится трудиться, Вы стараетесь постоянно себя развивать,'
                                                  ' но иногда наступают моменты, когда все,'
                                                  ' чего Вы хотите, это пойти куда-нибудь отдохнуть, выпить, развлечься'
                                                  '. У Вас есть слабое желание держать всё под своим контролем,'
                                                  ' редко, но у Вас возникают некие сомнения по поводу того,'
                                                  ' действительно ли Вы всё сделали правильно.'
                                                  ' Организовали что-либо достаточно хорошо.',
                                 reply_markup=check_main_menu_keyboard(message))

    else:
        bot.send_message(message.chat.id, 'Вы еще не закончили тестирование, '
                                          'поэтому ваших результатов у меня пока нет.')


@bot.message_handler(content_types=['text', 'voice', 'photo', 'audio'])
def answer_to_all(message):
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
