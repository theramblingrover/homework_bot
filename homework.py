import time
from pprint import pprint
from typing import Dict, Set, Any

import requests
import telegram
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import os

from requests import Response

load_dotenv('./homework.env')


@dataclass(frozen=True, init=False, repr=False)
class Tokens:
    PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')


tokens = Tokens()
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {tokens.PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> None:
    """Checks if all tokens got from .env"""

    print(asdict(tokens))
    if None in asdict(tokens).values():
        raise EnvironmentError("Data in .env is incorrect")


def send_message(bot, message):
    bot.send_message(tokens.TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Ask API about homeworks since timestamp"""

    params = {'from_date': timestamp}
    response: Response = requests.get(headers=HEADERS, url=ENDPOINT, params=params)
    return response.json()['homeworks']


def check_response(response):
    ...


def parse_status(homework):
    """Parses HW dict"""
    verdict = HOMEWORK_VERDICTS[homework['status']]
    homework_name = homework['lesson_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=tokens.TELEGRAM_TOKEN)
    timestamp = int(time.time())
    timestamp = 0

    ...

    while True:
        homeworks = get_api_answer(timestamp)
        for homework in homeworks:
            try:
                message = parse_status(homework)
                print(message)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
            send_message(bot=bot, message=message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
