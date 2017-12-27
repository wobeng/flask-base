from collections import OrderedDict

import simplejson
from flask import request


class GoogleJsonStyle:
    def __init__(self, parent, data, msg=None):
        self.parent = parent
        self.data = data or {}

        if msg:
            data['message'] = msg

    @staticmethod
    def add_count(data):
        for k in dict(data):
            if k.lower().endswith('count'):
                del data[k]
        data['currentItemCount'] = len(data['items']) if 'items' in data else 1
        return data

    @staticmethod
    def add_self(data):
        data['selfLink'] = request.url
        return data

    @staticmethod
    def add_next_link(data):
        if 'items' in data:
            if 'LastEvaluatedKey' in data:
                data['nextLink'] = request.url + '?start=' + data.pop('LastEvaluatedKey')
        return data

    def status_code(self):
        data = bool(self.data)
        codes = {
            True: {'POST': 201, 'OTHER': 200},
            False: {'POST': 201, 'GET': 404, 'OTHER': 204},
        }
        return codes.get(data).get(request.method, codes[data]['OTHER'])

    def add_edit_self(self, data):
        if hasattr(self.parent, 'put') or hasattr(self.parent, 'delete') or hasattr(self.parent, 'patch'):
            data['editLink'] = request.url
        return data

    def body(self):
        if not self.data:
            return ''
        body = self.add_count(self.data)
        body = self.add_self(body)
        body = self.add_edit_self(body)
        body = self.add_next_link(body)
        body = OrderedDict(body)
        body['items'] = body.pop('items')
        body = simplejson.dumps(body, indent=3)
        return body