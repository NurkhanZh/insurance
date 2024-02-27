class ClientBaseException(Exception):
    pass


class PersonNotFound(ClientBaseException):
    pass


class InternalServiceError(ClientBaseException):
    pass
