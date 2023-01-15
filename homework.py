import logging
import os
import sys
from http import HTTPStatus as HS
from time import time, sleep
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s,'
                              ' %(funcName)s, %(lineno)s')
handler = logging.StreamHandler(stream=sys.stdout)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
handler.setFormatter(formatter)


def send_message(bot, message):
    """Sends a message to chat."""
    logger.info('Trying to send message')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Message sent successfully')
    except Exception:
        logger.error('Failed to send message')
        raise Exception('Failed to send message')
    else:
        logger.debug('Message sent successfully')


def get_api_answer(current_timestamp):
    """Requests data from API."""
    timestamp = current_timestamp or time().__int__()
    try:
        logger.info('Sending request to API')
        responce = requests.get(ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
    except Exception as error:
        raise Exception(f'API request error: {error}')
    if responce.status_code != HS.OK:
        raise Exception(f'HTTP error {responce.status_code}')
    try:
        return responce.json()
    except ValueError:
        raise ValueError('Error converting json')


def check_response(response):
    """Checks if API returns correct data."""
    try:
        response['homeworks'] and response['current_date']
    except KeyError:
        raise KeyError('Unexpected dict format')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Wrong response format')
    try:
        homework = (response['homeworks'])[0]
        return homework
    except IndexError:
        raise IndexError('Homeworks list is empty')


def parse_status(homework):
    """Gets homework status from homework dict."""
    if 'homework_name' not in homework:
        raise KeyError('Key "homework_name" not found')
    if 'status' not in homework:
        raise Exception('Key "status" not found')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise Exception(f'Unknown status: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Returns False if at last one token is not found."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    current_timestamp = time().__int__()
    status_message = ''
    error_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if not check_tokens():
        logger.critical('No tokens found')
        sys.exit(1)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            message = parse_status(check_response(response))
            if message != status_message:
                send_message(bot, message)
                status_message = message
            else:
                logger.debug('Homework status unchanged since last check')
        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе программы: {error}'
            if message != error_message:
                send_message(bot, message)
                error_message = message
        finally:
            sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
