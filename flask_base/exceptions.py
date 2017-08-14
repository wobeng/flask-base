from py_utils.exceptions import Error


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
