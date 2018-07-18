from marshmallow import Schema
from marshmallow.fields import String, List
from marshmallow.validate import ContainsOnly


class CaseTestSchema:
    class ViewArg(Schema):
        app = String(required=True, example='cd8482612f04')
        path1 = String()

    class Header(Schema):
        xsrf = String(required=True, example='testing', attribute='csrf')

    class Get:
        class Query(Schema):
            get_query_id = List(String(), validate=ContainsOnly(('two', 'one')))

        class Header(Schema):
            get_header_id = String()

        class ViewArg(Schema):
            get_viewarg_id = String()

    class Post:
        class Body(Schema):
            post_body_id1 = String(required=True, example='testing missing1')
            post_body_id2 = String(example='testing missing2')

        class Query(Schema):
            post_query_id = String(example='testing example query')

        class Header(Schema):
            post_header_id = String()

        class ViewArg(Schema):
            post_viewarg_id = String()
