import json
import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HTTPRequestError

load_dotenv()


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('main.log')
file_handler.setLevel(logging.ERROR)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s '
    '| %(funcName)s | %(lineno)s | %(message)s'
)

file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICT = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Message send')
    except Exception as error:
        message = (
            f'{error}! Message: {message}'
            f'to chat: {TELEGRAM_CHAT_ID} not delivered'
        )
        logger.error(message, exc_info=True)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logger.info(
            f'Sending a request to {ENDPOINT} with parameters {params}'
        )
        if response.status_code != HTTPStatus.OK:
            message = (
                'Server did not return status 200.'
                f'Return status {response.status_code}'
            )
            logger.error(message)
            raise HTTPRequestError(response)
    except requests.ConnectionError as error:
        message = 'A Connection error occurred.'
        logger.error(error, message)
    except requests.Timeout as error:
        message = 'error Timeout'
        logger.error(error, message)
    except json.JSONDecodeError as error:
        message = 'Failed to read json object.'
        logger.error(error, message)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not response:
        message = 'Empty dictionary'
        logger.error(message)
        raise KeyError(message)

    if not isinstance(response, dict):
        message = (
            'Wrong type response.'
            f'Should have come dict but came {type(response)}'
        )
        logger.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'Key homeworks missing'
        logger.error(message)
        raise KeyError(message)

    homeworks_response = response.get('homeworks')
    if not isinstance(homeworks_response, list):
        message = (
            'Wrong type homeworks.'
            f'Should have come list but came {type(homeworks_response)}'
        )
        logger.error(message)
        raise TypeError(message)

    return response.get('homeworks')


def parse_status(homework):
    """Извлекает название и статус из конкретной домашней работы."""
    homework_name = homework.get('homework_name', 'Нет имени работы')
    homework_status = homework.get('status')
    if 'status' not in homework:
        message = 'Missing key status.'
        logger.error(message)
        raise KeyError(message)

    verdict = VERDICT.get(homework_status)
    if homework_status not in VERDICT:
        message = f'{homework_status} not among the possible'
        logger.error(message)
        raise KeyError(message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения необходимых для работы."""
    env_variable_value = []
    keys_variable_value = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }

    for token, _ in keys_variable_value.items():
        if keys_variable_value[token] is None:
            logger.error(f'{token} not found')
        env_variable_value.append(keys_variable_value[token])
    return all(env_variable_value)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'No required environment'
        logger.critical(message)
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
                logger.debug('Ответ API пуст: нет домашних работ.')
                continue
            for homework in homeworks:
                message = parse_status(homework)
                if last_send.get(homework['homework_name']) != message:
                    send_message(bot, message)
                    last_send[homework['homework_name']] = message
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_send['error'] != message:
                send_message(bot, message)
                last_send['error'] = message
        else:
            last_send['error'] = None
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
