import logging
import os
import time
import requests

from telebot import TeleBot
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


NOT_JSON = 'Ошибка формата, нужен JSON.'
EMPTY_LIST = 'Ошибка, словарь пуст.'
MESSAGE_SENDING_ERROR = 'Ошибка отправки сообщения.'


class NotJSONError(Exception):
    """Ошибка формата, когда не JSON."""

    pass


class TokensError(Exception):
    """Ошибка необходимых переменных."""

    pass


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""

    pass


def check_tokens():
    """Проверяет доступность необходимых переменных окружения."""
    for key in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if not key:
            logging.critical('Отсутствие обязательных переменных окружения.')
            return False
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        raise MessageSendingError(MESSAGE_SENDING_ERROR.format(
            error=error,
            message=message,
        ))
    logging.debug('Сообщение успешно отправлено.')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API."""
    timestamp = int(time.time())
    params = {'from_date': timestamp}
    parameters = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        return requests.get(parameters).json()
    except Exception as error:
        raise NotJSONError(NOT_JSON.format(error))


def check_response(response):
    """Проверяет ответ API."""
    if not isinstance(response, dict) or not isinstance(
        response.get('homeworks'), list
    ):
        message = 'Некорректный тип данных.'
        logging.error(message)
        raise TypeError(message)

    try:
        homework_list = response['homeworks']
    except KeyError:
        logging.error('Ошибка ключа homeworks.')
        raise KeyError('Ошибка ключа homeworks.')
    try:
        return homework_list[0]
    except IndexError:
        logging.debug('Пустой список работ.')
        raise IndexError(EMPTY_LIST)


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутствует ключ homework_name')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS[homework.get('status')]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise TokensError('Ошибка небходимыз переменных.')

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            bot.send_message(message)
            logging.info(homework)
        except Exception as error:
            logging.error(MESSAGE_SENDING_ERROR)
            message = f'Сбой в работе программы: {error}'
            bot.send_message(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    main()
