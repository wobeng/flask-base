from flask import request


class Error(Exception):
    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self, message)
        self.payload = payload
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {
            'error': {
                'code': self.status_code,
                'message': self.payload[0]['message'],
                'errors': self.payload
            }
        }


class ClientError(Error):
    def __init__(self, messages, domain=None):
        payload = []
        if isinstance(messages, str):
            messages = [messages]
        for message in messages:
            payload.append(
                {
                    'domain': domain or request.endpoint,
                    'reason': message,
                    'message': message
                }
            )
        Error.__init__(self, 'ClientErrorException', 400, payload)


class Schema(Error):
    def __init__(self, errors, domain):
        payload = []
        for parent_e, parent_e_val in errors.items():
            for child_e, messages in parent_e_val.items():
                for message in messages:
                    payload.append(
                        {
                            'domain': domain,
                            'locationType': self.__class__.__name__.lower(),
                            'location': child_e,
                            'locationId': str(parent_e),
                            "reason": message,
                            'message': message
                        }
                    )
        Error.__init__(self, 'SchemaFieldsException', 400, payload)


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
