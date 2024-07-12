import logging
import os
import sys
import time
from pathlib import Path

import requests
from telebot import TeleBot
from dotenv import load_dotenv

import exceptions

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
    """Проверяет доступность необходимых переменных окружения."""
    for key in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if not key:
            logging.critical(
                f'Отсутствие обязательных переменных окружения: {key}'
            )
            return False
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        logging.error('Ошибка отправки сообщения.')
    else:
        logging.debug('Сообщение успешно отправлено!')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API."""
    try:
        parameters = requests.get(
            url=ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if parameters.status_code == 200:
            return parameters.json()
        raise exceptions.WrongStatusError('API домашки отличается от 200.')
    except requests.RequestException as error:
        logger.info(error)
    except Exception as error:
        NOT_JSON = 'Ошибка формата, нужен JSON.'
        raise exceptions.NotJSONError(NOT_JSON.format(error))


def check_response(response):
    """Проверяет ответ API."""
    if not isinstance(response, dict):
        raise TypeError('Поступили данные вида, отличного от словаря.')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Поступили данные вида, отличного от списка.')
    homeworks_list = response['homeworks']
    if homeworks_list == []:
        logging.debug('Статус работы не изменился.')

    if 'homeworks' in response:
        return homeworks_list[0]
    else:
        raise KeyError('Ошибка ключа homeworks.')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутствует название работы.')
    if 'status' not in homework:
        raise KeyError('В ответе отсутствует статус работы.')
    homework_name = homework['homework_name']
    status = homework['status']
    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
    else:
        raise exceptions.ParseStatusError('Передан неизвестный статус работы.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise exceptions.TokensError('Ошибка небходимых переменных.')

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        current_date = timestamp
        try:
            response = get_api_answer(current_date)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=f'{Path(__file__).stem}.log',
        format='%(asctime)s [%(levelname)s] %(message)s\n\
                %(funcName)s %(lineno)d',
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    main()
