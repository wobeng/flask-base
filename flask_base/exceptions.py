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
    def __init__(self, messages, status_code=400, domain=None):
        payload = []
        if isinstance(messages, str):
            messages = [messages]
        for message in messages:
            payload.append(
                {
                    'domain': (domain or request.endpoint).split('.')[-1],
                    'reason': message,
                    'message': message
                }
            )
        Error.__init__(self, 'ClientErrorException', status_code, payload)


class Schema(Error):
    payload = []

    def __init__(self, errors, domain):
        self.payload = []
        self.domain = domain

        for parent_e, parent_e_val in errors.items():
            if isinstance(parent_e_val, list):
                for message in parent_e_val:
                    self.to_payload(parent_e, 0, message)
            else:
                for child_e, messages in parent_e_val.items():
                    for message in messages:
                        self.to_payload(child_e, parent_e, message)
        Error.__init__(self, 'SchemaFieldsException', 400, self.payload)

    def to_payload(self, location, location_id, message):
        self.payload.append(
            {
                'domain': self.domain,
                'locationType': self.__class__.__name__.lower(),
                'location': location,
                'locationId': location_id,
                "reason": message,
                'message': message
            }
        )


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
