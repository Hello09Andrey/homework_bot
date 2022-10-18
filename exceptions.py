class HTTPRequestError(Exception):
    """Если нет ответа от сервера возвращает."""

    def __init__(self, response):
        """Возвращает код ответа API."""
        message = (
            f'Эндпоинт {response.url} недоступен. '
            f'Код ответа API: {response.status_code}]'
        )
        super().__init__(message)


class MessageNotSend(Exception):
    """Если сообщение не было отправлено."""

    def __init__(self, error, TELEGRAM_CHAT_ID, message):
        """Сообщение которое будет отправлено."""
        err_message = (
            f'{error}!!! Message: {message}'
            f'to chat: {TELEGRAM_CHAT_ID} not delivered'
        )
        super().__init__(err_message)


class ServerError(Exception):
    """Если ендплоид API не отвечает."""

    pass
