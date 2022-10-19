class HTTPRequestError(Exception):
    """Если нет ответа от сервера возвращает."""

    pass


class MessageNotSend(Exception):
    """Если сообщение не было отправлено."""

    pass


class ServerError(Exception):
    """Если ендплоид API не отвечает."""

    pass
