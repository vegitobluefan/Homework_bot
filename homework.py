import logging
import os
import sys
import time
import requests
from http import HTTPStatus

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


logging.basicConfig(
    level=logging.DEBUG,
    filename='./homework_log.log',
    format='%(asctime)s [%(levelname)s] %(message)s',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


class NotJSONError(Exception):
    """Ошибка формата, когда не JSON."""

    pass


class TokensError(Exception):
    """Ошибка необходимых переменных."""

    pass


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""

    pass


class WrongStatusError(Exception):
    """Когда API домашки возвращает код, отличный от 200."""

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
    params = {'from_date': timestamp}
    try:
        parameters = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        logging.info(error)

    if parameters.status_code != HTTPStatus.OK:
        message = 'API домашки возвращает код, отличный от 200.'
        logging.error(message)
        raise WrongStatusError(message)
    try:
        return parameters.json()
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
        raise KeyError('В ответе отсутствует название работы.')

    homework_name = homework['homework_name']
    status = homework['status']
    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('В ответе отсутствует статус работы.')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise TokensError('Ошибка небходимыз переменных.')

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = '2024-05-23T06:55:14Z' # int(time.time())
    current_status = ''
    current_error = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if not len(homework):
                logging.info('Статус работы не изменён.')
            else:
                message = parse_status(homework[0])
                send_message(bot, message)
                if current_status == message:
                    logging.info(homework)
                else:
                    current_status = message
                    send_message(bot, message)
        except Exception as error:
            logging.error(MESSAGE_SENDING_ERROR)
            message = f'Сбой в работе программы: {error}'
            if current_error != str(error):
                current_error = str(error)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
