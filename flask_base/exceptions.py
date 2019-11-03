class Error(Exception):
    code = 400
    msg = 'Something went wrong'
    error_type = 'ApiException'

    def __init__(self, message=None, status_code=None, payload=None, error_type=None):
        message = message or self.msg
        super(Error, self).__init__(message)
        self.payload = payload or []
        self.message = message
        self.error_type = error_type or self.error_type
        self.status_code = status_code or self.code

    def to_dict(self):
        output = {
            'error': {
                'code': self.status_code,
                'message': self.message,
                'error_type': self.error_type
            }
        }
        if self.payload:
            output['error']['errors'] = self.payload
        return output


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
        super(Schema, self).__init__('Request input schema is invalid', 400, self.payload, 'SchemaFieldsException')

    def to_payload(self, location, location_id, message):
        self.payload.append(
            {
                'domain': self.domain.lower(),
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
