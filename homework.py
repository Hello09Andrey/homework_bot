import os
import time
import telegram
import logging
from http import HTTPStatus
from exceptions import HTTPRequestError
import requests

from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
payload = {'from_date': 1664730000}

HOMEWORK_STATUSES = {
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
        logging.error(error, exc_info=True)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    logging.info(f'Sending a request to {ENDPOINT} with parameters {params}')
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError(response)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not response:
        message = 'Empty dictionary'
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response, dict):
        message = 'Wrong type response'
        logging.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'Key homeworks missing'
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response.get('homeworks'), list):
        message = 'Wrong type homeworks'
        logging.error(message)
        raise TypeError(message)

    return response.get('homeworks')


def parse_status(homework):
    """Извлекает название и статус из конкретной домашней работы."""
    if not homework.get('homework_name'):
        logging.error('Missing homework name.')
        homework_name = 'Noname'
    else:
        homework_name = homework.get('homework_name')

    homework_status = homework.get('status')
    if 'status' not in homework:
        message = 'Missing key status.'
        logging.error(message)
        raise KeyError(message)

    verdict = HOMEWORK_STATUSES.get(homework_status)
    if homework_status not in HOMEWORK_STATUSES:
        message = f'{homework_status} not among the possible'
        logging.error(message)
        raise KeyError(message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения необходимых для работы."""
    list_env = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    return all(list_env)


def main():
    """Основная логика работы бота."""
    last_send = {
        'error': None,
    }

    if not check_tokens():
        logging.critical('No required environment')
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    response = get_api_answer(current_timestamp)
    homeworks = check_response(response)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logging.debug('Ответ API пуст: нет домашних работ.')
                break
            for homework in homeworks:
                message = parse_status(homework)
                if last_send.get(homework['homework_name']) != message:
                    send_message(bot, message)
                    last_send[homework['homework_name']] = message
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
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
