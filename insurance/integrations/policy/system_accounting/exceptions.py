class BaseAdapterError(Exception):
    message: str = ''

    def __init__(self, message='', **kwargs):
        self.message = (message or self.message).format(**kwargs)

    def __str__(self):
        return self.message


class UnknownAdapterError(BaseAdapterError):
    message = 'Неизвестная ошибка адаптера'


class DecodeJsonError(BaseAdapterError):
    message = 'Ошибка декодирования JSON. content_type:{content_type}, content:{content}'


class ResponseAdapterError(BaseAdapterError):
    message = 'Ошибка ответа адаптера. {detail}'
