# Проект Бот-ассистент
Данный проект представляет собой Telegram-бота, который обращается к API сервиса Практикум Домашка и узнаваёт статус домашней работы: взята ли домашка в ревью, проверена ли она, а если проверена — принял её ревьюер или вернул на доработку.

## Что умеет делать бот:
- Раз в 10 минут опрашивает API сервиса Практикум Домашка и проверяет статус отправленной на ревью домашней работы
- При обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram
- Логирует свою работу и сообщает о важных проблемах сообщением в Telegram

## Функции, описанные в проекте:
- Функция main() — в ней описана основная логика работы программы. Все остальные функции должны запускаться из неё.                
Последовательность действий в общем виде такая:
Сделать запрос к API, проверить ответ, если есть обновления — получить статус работы из обновления и отправить сообщение в Telegram, родождать некоторое время и вернуться в пункт 1.

- Функция check_tokens() проверяет доступность переменных окружения, которые необходимы для работы программы. Если отсутствует хотя бы одна переменная окружения — продолжать работу бота нет смысла.

- Функция get_api_answer() делает запрос к единственному эндпоинту API-сервиса. В качестве параметра в функцию передаётся временная метка. В случае успешного запроса должна вернуть ответ API, приведя его из формата JSON к типам данных Python.

- Функция check_response() проверяет ответ API на соответствие документации из урока «API сервиса Практикум Домашка». В качестве параметра функция получает ответ API, приведённый к типам данных Python.

- Функция parse_status() извлекает из информации о конкретной домашней работе статус этой работы. В качестве параметра функция получает только один элемент из списка домашних работ. В случае успеха функция возвращает подготовленную для отправки в Telegram строку, содержащую один из вердиктов словаря HOMEWORK_VERDICTS.

- Функция send_message() отправляет сообщение в Telegram-чат, определяемый переменной окружения TELEGRAM_CHAT_ID. Принимает на вход два параметра: экземпляр класса TeleBot и строку с текстом сообщения.
## Разработчик: [Аринов Данияр](https://github.com/vegitobluefan)
