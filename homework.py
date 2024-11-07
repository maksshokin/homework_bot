
from http import HTTPStatus
import logging
import os
import sys
import time

from dotenv import load_dotenv
from pytest import warns
import requests
from telebot import TeleBot

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


def check_tokens():
    """Проверка доступности переменных окружения."""
    if (
        len(PRACTICUM_TOKEN) != 0 and
        len(TELEGRAM_TOKEN) != 0 and
        len(TELEGRAM_CHAT_ID) != 0
    ):
        return True
    else:
        logging.critical()
        sys.exit()



def send_message(bot, message):
    """Отправка сообщения."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(local_time):
    """Получить статус домашней работы."""
    api_answer = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': local_time}
    )
    if api_answer.status_code == HTTPStatus.OK:
        return api_answer.json()


def check_response(response):
    """Проверить валидность ответа."""
    return response.get('homeworks')


def parse_status(status):
    """Узнать статус."""
    if 'homework_name' in status.get():
        return status.get('status')


def main():
    """Основная логика работы."""
    if check_tokens():
        bot = TeleBot(token=TELEGRAM_TOKEN)
        while True:
            try:
                response = get_api_answer(int(time.time()))
                print(response)
                message = check_response(response)
                print(message)
                send_message(bot, message)
            finally:
                time.sleep(600)

if __name__ == "__main__":
    main()