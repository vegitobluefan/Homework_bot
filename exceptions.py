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


class ParseStatusError(Exception):
    """Ошибка статуса."""

    pass
