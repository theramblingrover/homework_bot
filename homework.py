import logging
import os
import sys
import time
from http import HTTPStatus as HS

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD: int = 60 * 10
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(level=logging.DEBUG, format=('%(asctime)s, %(levelname)s, '
                    '%(message)s, %(funcName)s, %(lineno)s'),
                    handlers=[logging.FileHandler('homework.log'),
                              logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Sends a message to chat."""
    logger.info('Trying to send message')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        logger.error(f'Failed to send message: {message}')
    else:
        logger.debug(f'Message sent successfully: {message}')


def get_api_answer(timestamp: int) -> dict:
    """Requests data from API."""
    try:
        logger.info('Sending request to API')
        params = {'from_date': timestamp}
        responce = requests.get(ENDPOINT, params, headers=HEADERS, timeout=90)
        if responce.status_code != HS.OK:
            raise exceptions.InfoError(
                f'HTTP error {ENDPOINT}, {HEADERS}, {params}, '
                f'{responce.status_code}, {responce.text}, {responce.reason}'
            )
        return responce.json()
    except Exception as error:
        raise exceptions.InfoError(f'API request error: {error}')


def check_response(response: dict) -> list:
    """Checks if API returns correct data."""
    if not isinstance(response, dict):
        raise TypeError('Wrong response format: <dict> expected.')
    if 'homeworks' not in response:
        raise exceptions.InfoError('Keys are not found in response')
    if 'current_date' not in response:
        raise exceptions.InfoError('Keys are not found in response')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Wrong response format: <list> expected.')
    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Gets homework status from homework dict."""
    if 'homework_name' not in homework:
        raise exceptions.InfoError('Key "homework_name" not found')
    if 'status' not in homework:
        raise exceptions.InfoError('Key "status" not found')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise exceptions.InfoError(f'Unknown status: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Returns False if at least one token is not found."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    last_status_message = ''
    last_error_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if not check_tokens():
        logger.critical('No tokens found.')
        sys.exit(1)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homeworks_list = check_response(response)
            if homeworks_list != []:
                status_message = parse_status(homeworks_list[0])
            else:
                status_message = 'Не найдено работ на проверке'
            if status_message != last_status_message:
                send_message(bot, status_message)
                last_status_message = status_message
            else:
                logger.debug('Homework status unchanged since last check')
        except exceptions.SilentError as error:
            logger.error(f'Error occured: {error}')
        except (exceptions.InfoError, TypeError) as error:
            logger.error(f'Error occured: {error}. Error message sent to chat')
            error_message = f'Произошла ошибка: {error}'
            if error_message != last_error_message:
                send_message(bot, error_message)
                last_error_message = error_message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

# Как тебя в Пачке найти? Куратор этот мой вопрос игнорит.
