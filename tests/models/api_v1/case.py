from marshmallow import Schema
from marshmallow.fields import String, List
from marshmallow.validate import ContainsOnly


class CaseTestSchema:
    class ViewArg(Schema):
        app = String(required=True, default='cd8482612f04')
        path1 = String()

    class Get:
        class Body(Schema):
            get_body_id = String()

        class Query(Schema):
            get_query_id = List(String, validate=ContainsOnly(('two', 'one')))

        class Header(Schema):
            get_header_id = String()

        class ViewArg(Schema):
            get_viewarg_id = String()

    class Post:
        class Body(Schema):
            post_body_id = String()

        class Query(Schema):
            post_query_id = String()

        class Header(Schema):
            post_header_id = String()

        class ViewArg(Schema):
            post_viewarg_id = String()
