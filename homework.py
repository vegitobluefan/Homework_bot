import logging
import os
import sys
import time
from pathlib import Path

import requests
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
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
    keys = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    }

    keys_checked = [key_name for key_name, key in keys.items() if key is None]
    if keys_checked:
        logging.critical(
            f'Отсутсвуют обязательные переменные окружения: {keys_checked}'
        )
    return keys_checked


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except (requests.RequestException or ApiTelegramException) as error:
        logging.error(f'Ошибка отправки сообщения: {error}')
    else:
        logging.debug('Сообщение успешно отправлено!')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API."""
    try:
        parameters = requests.get(
            url=ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if parameters.status_code != 200:
            raise exceptions.WrongStatusError('Статус отличается от 200.')
        return parameters.json()
    except requests.JSONDecodeError as error:
        raise exceptions.NotJSONError(
            f'Не получен ожидаемый JSON-объект: {error}'
        )
    except requests.RequestException as error:
        raise exceptions.RequestError(f'Ошибка запроса API: {error}')


def check_response(response):
    """Проверяет ответ API."""
    if not isinstance(response, dict):
        raise TypeError('Поступили данные вида, отличного от словаря.')
    if 'homeworks' not in response:
        raise KeyError('Ошибка ключа homeworks.')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Поступили данные типа, отличного от list.')
    if 'current_date' not in response:
        raise exceptions.NoCurrentDateError('Ключ current_date отсутствует.')
    if not isinstance(response.get('current_date'), int):
        raise exceptions.NotIntCurrentDateError(
            'Тип ключа current_date отличен от int'
        )

    return response['homeworks']


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутствует название работы.')
    if 'status' not in homework:
        raise KeyError('В ответе отсутствует статус работы.')
    homework_name = homework['homework_name']
    status = homework['status']

    if status not in HOMEWORK_VERDICTS:
        raise ValueError('Передан неизвестный статус работы.')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens():
        raise exceptions.TokensError('Ошибка небходимых переменных.')

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                new_status = parse_status(homework[0])
            else:
                new_status = 'Статус домашки не изменился.'
            if new_status != last_status:
                send_message(bot, new_status)
                logger.info(new_status)
                last_status = new_status
            timestamp = response.get('current_date', timestamp)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if (
                error != exceptions.NoCurrentDateError
                or error != exceptions.NotIntCurrentDateError
            ):
                if last_status != str(error):
                    send_message(bot, message)
                    last_status = str(error)
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
