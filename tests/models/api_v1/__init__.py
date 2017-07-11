from marshmallow import Schema, fields


class BaseSchema(Schema):
    class Body(Schema):
        body_id2 = fields.String()

    class Query(Schema):
        query_id2 = fields.String()

    class Header(Schema):
        header_id2 = fields.String()

    class ViewArg(Schema):
        path2 = fields.String()
