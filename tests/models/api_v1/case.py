from tests.models.api_v1 import Base, Schema, fields


class CaseTestSchema(Base):
    class Get:
        class Body(Schema):
            body_id = fields.String()

        class Query(Schema):
            query_id = fields.String()

        class Header(Schema):
            header_id = fields.String()

        class Cookie(Schema):
            cookie_id = fields.String()

        class ViewArg(Schema):
            path1 = fields.String()

    class Post:
        class Body(Schema):
            body_id = fields.String()

        class Query(Schema):
            query_id = fields.String()

        class Header(Schema):
            header_id = fields.String()

        class Cookie(Schema):
            cookie_id = fields.String()

        class ViewArg(Schema):
            path1 = fields.String()
