from flask import jsonify, g

from tests.apps.api_v1 import Api, api
from tests.models.api_v1.case import CaseTestSchema


class CaseTest(Api):
    schema = CaseTestSchema

    def get(self, body, query, path1, path2):
        return jsonify(body, query, path1, path2)

    def post(self, body, query, path1, path2):
        return jsonify(body, query, path1, path2)


api.add_url_rule('/case/test', view_func=CaseTest.as_view('casetest'))
