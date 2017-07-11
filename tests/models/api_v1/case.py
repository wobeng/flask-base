from tests.models.api_v1 import BaseSchema, Schema, fields


class CaseTestSchema(BaseSchema):
    class Get:
        class Body(Schema):
            get_body_id = fields.String()

        class Query(Schema):
            get_query_id = fields.String()

        class Header(Schema):
            get_header_id = fields.String()

        class Cookie(Schema):
            get_cookie_id = fields.String()

        class ViewArg(Schema):
            get_path1 = fields.String()

    class Post:
        class Body(Schema):
            post_body_id = fields.String()

        class Query(Schema):
            post_query_id = fields.String()

        class Header(Schema):
            post_header_id = fields.String()

        class Cookie(Schema):
            post_cookie_id = fields.String()

        class ViewArg(Schema):
            post_path1 = fields.String()
