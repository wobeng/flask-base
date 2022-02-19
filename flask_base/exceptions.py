from flask import jsonify


class Error(Exception):
    code = 400
    msg = "Something went wrong"
    error_type = "ApiException"

    def __init__(
        self,
        message=None,
        status_code=None,
        payload=None,
        error_type=None,
        reason=None,
    ):
        message = str(message or self.msg)
        super(Error, self).__init__(message)
        self.payload = payload or []
        self.message = message
        self.error_type = error_type or self.error_type
        self.status_code = status_code or self.code
        self.reason = reason or {}

    def to_dict(self):
        output = {
            "error": {
                "code": self.status_code,
                "message": self.message,
                "error_type": self.error_type,
                "reason": self.reason,
            }
        }
        if self.payload:
            output["error"]["errors"] = self.payload
            output["error"]["reason"] = self.payload[0]["reason"]
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
        reason = None
        for key, value in self.flatten_dict(errors).items():
            if isinstance(value, list):
                message = value[0]
                if len(value) == 2:
                    reason = value[1]
            else:
                message = str(value)
            self.to_payload(key, key, message, reason=reason)
        super(Schema, self).__init__(
            "Request input schema is invalid",
            400,
            self.payload,
            "SchemaFieldsException",
        )

    @staticmethod
    def flatten_dict(d):
        def expand(key, value):
            if isinstance(value, dict):
                return [
                    (str(key) + "." + str(k), v)
                    for k, v in Schema.flatten_dict(value).items()
                ]
            else:
                return [(key, value)]

        items = [item for k, v in d.items() for item in expand(k, v)]

        return dict(items)

    def to_payload(
        self, location, location_id, message, parent=None, reason=None
    ):
        error = {
            "domain": self.domain.lower(),
            "locationType": self.__class__.__name__.lower(),
            "location": location,
            "locationId": location_id,
            "reason": reason or message,
            "message": message,
        }
        if parent:
            error["parent"] = parent
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
