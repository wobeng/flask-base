from marshmallow import Schema
from py_utils.mmallow import String, List, ContainsOnly


class CasePat2Schema:
    class Header(Schema):
        get_header_id = String()

    class ViewArg(Schema):
        get_viewarg_id = String()


class CaseTestSchema:
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
