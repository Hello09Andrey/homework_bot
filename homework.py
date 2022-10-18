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
handlers = [file_handler, stdout_handler]

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS_HOME_WORKS = {
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
        raise MessageNotSend(error, TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logging.info(
            f'Sending a request to {ENDPOINT} with parameters {params}'
        )
    except Exception as error:
        raise ServerError(error)
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError(response)
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

    homeworks_response = response.get('homeworks')
    if not isinstance(homeworks_response, list):
        raise TypeError(
            'Wrong type homeworks.'
            f'Should have come list but came {type(homeworks_response)}'
        )

    return homeworks_response


def parse_status(homework):
    """Извлекает название и статус из конкретной домашней работы."""
    name = homework['homework_name']
    if 'homework_name' not in homework:
        message = 'Missing key \'homework_name\'.'
        raise KeyError(message)

    status = homework['status']
    if 'status' not in homework:
        message = 'Missing key status.'
        raise KeyError(message)

    verdict = VERDICTS_HOME_WORKS.get(status)
    if status not in VERDICTS_HOME_WORKS:
        message = f'{status} not among the possible'
        raise KeyError(message)

    return f'Изменился статус проверки работы "{name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения необходимых для работы."""
    variable_availability = True
    keys_variable_value = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }

    for token in keys_variable_value:
        if keys_variable_value[token] is None:
            logging.error(f'{token} not found')
            variable_availability = False
    return variable_availability


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'No required environment'
        raise KeyError(message)

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
        handlers=handlers

    )
    main()
