
from asyncio import exceptions
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
    if all([
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID 
    ]):
        return True
    else:
        logging.critical(f'Нет всех переменных')
        sys.exit()



def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error(f'Сообщение не отправлено, из-за ошибки.')
        raise Exception
    else:
        logging.debug(f'Сообщение отправлено: {message}')


def get_api_answer(local_time):
    """Получить статус домашней работы."""
    try:
        api_answer = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': local_time}
        )
        if api_answer.status_code == HTTPStatus.OK:
            return api_answer.json()
        else:
            raise exceptions.InvalidResponseCode()
    except Exception:
        raise requests.RequestException()


def check_response(response):
    """Проверить валидность ответа."""
    if not isinstance(response, dict):
        raise TypeError()
    if 'homeworks' in response:
        homeworks = response.get('homeworks')
    else:
        raise exceptions.EmptyResponseFromAPI('Пустой API')
    if not isinstance(homeworks, list):
        raise TypeError()
    return homeworks


def parse_status(status):
    """Узнать статус."""
    homework = status.get()
    if 'homework_name' in homework:
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
    logging.basicConfig(level=logging.INFO)
    main()