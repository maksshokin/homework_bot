import os
import sys
import time

import logging
import requests

from asyncio import exceptions
from dotenv import load_dotenv
from telebot import TeleBot
from http import HTTPStatus


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
        logging.critical('Нет всех переменных')
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error('Сообщение не отправлено, из-за ошибки.')
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
        raise exceptions.ConnectinError()


def check_response(response):
    """Проверить валидность ответа."""
    if not isinstance(response, dict):
        raise TypeError(
            'Ошибка в типе API.'
            f'{response}, type - {type(response)}'
        )
    if not 'homeworks' in response:
        raise exceptions.AttributeError('Пустой API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            'homeworks not list.'
            f'{homeworks}, type -{type(homeworks)}'
        )
    return homeworks


def parse_status(status):
    """Узнать статус."""
    if not 'homework_name' in status:
        raise KeyError('Нет ключа homework_name.')
    verdict = status.get('status')
    homework_name = status.get('homework_name')
    if not verdict in HOMEWORK_VERDICTS:
        raise ValueError('Неизвестный статус работы.')
    return (
        f'Изменился статус проверки работы "{homework_name}".'
        f' {HOMEWORK_VERDICTS[verdict]}'
    )


def main():
    """Основа."""
    if check_tokens():
        bot = TeleBot(token=TELEGRAM_TOKEN)
        prev_message = ''
        prev_status = ''
        while True:
            try:
                response = get_api_answer(int(time.time()))
                message = check_response(response)
                if not response['homeworks']:
                    logging.debug('Нет активных работ.')
                    message = 'Нет активных работ.'
                else:
                    current_status = message[0].get('status')
                if current_status != prev_status:
                    message = f'{HOMEWORK_VERDICTS[current_status]}'
                    prev_status = current_status
                if prev_message != message:
                    send_message(bot, message)
                    prev_message = message
            finally:
                time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
