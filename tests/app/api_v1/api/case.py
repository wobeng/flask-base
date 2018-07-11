from flask import jsonify

from tests.app.api_v1.api import Api, api
from tests.app.api_v1.models.case import CaseTestSchema


class CaseTest(Api):
    schema = CaseTestSchema

    def get(self, query, path1, path2):
        return self.success({
            'query': query,
            'path1': path1,
            'path2': path2
        })

    def post(self, body, query, path1, path2):
        return jsonify(body, query, path1, path2)


api.add_url_rule('/case/test', view_func=CaseTest.as_view('casetest'))
