import simplejson
from flask import make_response
from flask.views import MethodView


class Base(MethodView):
    @staticmethod
    def jsonify(data):
        data = simplejson.dumps(data, indent=3)
        response = make_response(data)
        response.headers['Content-Type'] = 'application/json'
        return response
