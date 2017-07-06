class ClientError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class VidaException(ClientError):
    pass


class Schema(VidaException):
    pass


class Header(VidaException):
    pass


class Path(VidaException):
    pass


class Query(VidaException):
    pass


class Cookie(VidaException):
    pass


class ViewArg(VidaException):
    pass


class Body(VidaException):
    pass
