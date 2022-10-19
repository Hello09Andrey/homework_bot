import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HTTPRequestError, MessageNotSend, ServerError

load_dotenv()

file_handler = logging.FileHandler(filename='main.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKEN_NAMES = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Message send')
    except Exception as error:
        raise MessageNotSend(
            f'{error}!!! Message: {message}'
            f'to chat: {TELEGRAM_CHAT_ID} not delivered'
        )


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    try:
        logging.info(
            f'Sending a request to {ENDPOINT} with parameters {params}'
        )
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise ServerError(
            f'{error}!!! Adress: {ENDPOINT}'
            f' with headers: {HEADERS} and'
            f' parameters: {params} does not answer'
        )
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError(
            f'Эндпоинт {response.url} недоступен. '
            f'Код ответа API: {response.status_code}]'
        )
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not response:
        raise KeyError('Empty dictionary')

    if not isinstance(response, dict):
        raise TypeError(
            'Wrong type response.'
            f'Should have come dict but came {type(response)}'
        )

    if 'homeworks' not in response:
        raise KeyError('Key homeworks missing')

    homeworks_response = response['homeworks']
    if not isinstance(homeworks_response, list):
        raise TypeError(
            'Wrong type homeworks.'
            f'Should have come list but came {type(homeworks_response)}'
        )

    return homeworks_response


def parse_status(homework):
    """Извлекает название и статус из конкретной домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('Missing key \'homework_name\'.')
    name = homework['homework_name']

    if 'status' not in homework:
        raise KeyError('Missing key status.')
    status = homework['status']

    if status not in HOMEWORK_VERDICTS:
        raise KeyError(f'{status} not among the possible')
    verdict = HOMEWORK_VERDICTS.get(status)

    return f'Изменился статус проверки работы "{name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения необходимых для работы."""
    variable_availability = True
    for i in TOKEN_NAMES:
        if globals()[i] is None:
            logging.error(f'{i} not found')
            variable_availability = False
    return variable_availability


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise KeyError('No required environment')

    last_send = {
        'error': None,
    }

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logging.debug('Ответ API пуст: нет домашних работ.')
                continue
            for homework in homeworks:
                message = parse_status(homework)
                if last_send.get(homework['homework_name']) != message:
                    send_message(bot, message)
                    last_send[homework['homework_name']] = message
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if last_send['error'] != message:
                send_message(bot, message)
                last_send['error'] = message
        else:
            last_send['error'] = None
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(name)s | %(levelname)s '
               '| %(funcName)s | %(lineno)s | %(message)s',
        handlers=[file_handler, stdout_handler]

    )
    main()
