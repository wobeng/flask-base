from flask import jsonify


class Error(Exception):
    code = 400
    msg = 'Something went wrong'
    error_type = 'ApiException'

    def __init__(self, message=None, status_code=None, payload=None, error_type=None, reason=None):
        message = message or self.msg
        super(Error, self).__init__(message)
        self.payload = payload or []
        self.message = message
        self.error_type = error_type or self.error_type
        self.status_code = status_code or self.code
        self.reason = reason or self.reason

    def to_dict(self):
        output = {
            'error': {
                'code': self.status_code,
                'message': self.message,
                'error_type': self.error_type,
                'reason': self.reason
            }
        }
        if self.payload:
            output['error']['errors'] = self.payload
            output['error']['reason'] = self.payload[0]['reason']
        return output

    def response(self):
        response = jsonify(self.to_dict())
        response.status_code = self.status_code
        return response


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
                for child_e, fields in parent_e_val.items():
                    if isinstance(fields, dict):
                        for field, message in fields.items():
                            self.to_payload(field, child_e, message[0], parent=parent_e)
                    else:
                        self.to_payload(child_e, 0, fields[0], parent=parent_e)
        super(Schema, self).__init__('Request input schema is invalid', 400, self.payload, 'SchemaFieldsException')

    def to_payload(self, location, location_id, message, parent=None):
        error = {
            'domain': self.domain.lower(),
            'locationType': self.__class__.__name__.lower(),
            'location': location,
            'locationId': location_id,
            "reason": message,
            'message': message
        }
        if parent:
            error['parent'] = parent
        self.payload.append(error)


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
