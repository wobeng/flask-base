import json
from collections import OrderedDict
from urllib.parse import urlencode

import simplejson
from flask import request, g
from werkzeug.urls import iri_to_uri


class GoogleJsonStyle:
    def __init__(self, parent, data, msg=None):
        self.parent = parent
        self.data = data or {}
        if msg:
            self.data['message'] = msg
        if 'Items' in self.data:
            self.data['items'] = self.data.pop('Items')

    @staticmethod
    def add_count(data):
        for k in dict(data):
            if k.lower().endswith('count'):
                del data[k]
        if 'items' in data:
            data['currentItemCount'] = len(data['items'])
        return data

    @staticmethod
    def add_self(data):
        callback = request.args.get('callback', '')
        data['selfLink'] = iri_to_uri(request.url).replace('?callback=' + callback, '').replace('&callback=' + callback,
                                                                                                '')
        return data

    @staticmethod
    def add_next_link(data):
        if 'items' in data:
            if 'LastEvaluatedKey' in data:
                query = dict(g.incoming_data.get('query', {}))
                query.pop('start', None)  # delete old start key
                query = '&'.join('{}={}'.format(key, val[0]) for key, val in query.items())
                query = '&' + query if query else query  # add & if not empty
                start = urlencode({'start': json.dumps(data.pop('LastEvaluatedKey'))})
                data['nextLink'] = request.base_url + '?' + start + query
        return data

    @staticmethod
    def content_type():
        if request.args.get('callback'):
            return 'application/javascript'
        else:
            return 'application/json'

    def status_code(self):
        data = bool(self.data)
        codes = {
            True: {'POST': 201, 'OTHER': 200},
            False: {'POST': 201, 'GET': 404, 'OTHER': 204},
        }
        return codes.get(data).get(request.method, codes[data]['OTHER'])

    def add_edit_self(self, data):
        if hasattr(self.parent, 'put') or hasattr(self.parent, 'delete') or hasattr(self.parent, 'patch'):
            data['editLink'] = request.base_url
        return data

    def body(self):
        if not self.data:
            return ''
        body = self.add_count(self.data)
        body = self.add_self(body)
        body = self.add_edit_self(body)
        body = self.add_next_link(body)
        body = OrderedDict(body)
        if 'items' in body:
            body['items'] = body.pop('items')
        body = simplejson.dumps({'data': body}, indent=3)
        if request.args.get('callback'):
            body = '{}({});'.format(request.args.get('callback'), body)
        return body
