class VehicleBaseException(Exception):
    pass


class VehicleNotFound(VehicleBaseException):
    pass


class InternalServiceError(VehicleBaseException):
    pass
