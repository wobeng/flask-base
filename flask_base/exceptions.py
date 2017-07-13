import simplejson
from flask import make_response


class ClientError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        if isinstance(self.message, dict):
            return self.message
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

    @staticmethod
    def jsonify(data):
        data = simplejson.dumps(data, indent=3)
        response = make_response(data)
        response.headers['Content-Type'] = 'application/json'
        return response


class Schema(ClientError):
    pass


class Header(Schema):
    pass


class Path(Schema):
    pass


class Query(Schema):
    pass


class ViewArg(Schema):
    pass


class Body(Schema):
    pass
