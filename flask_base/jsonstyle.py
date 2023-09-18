import json
from collections import OrderedDict

from flask import request
from werkzeug.urls import iri_to_uri
import base64
from py_tools.format import dumps
import gzip

def encode_json(data):
    json_string = json.dumps(data, separators=(',', ':'))
    compressed_data = gzip.compress(json_string.encode())
    base64_url_safe = base64.urlsafe_b64encode(compressed_data).decode()
    return base64_url_safe

def decode_json(data):
    decoded_bytes = base64.urlsafe_b64decode(data.encode())
    decoded_bytes = gzip.decompress(decoded_bytes)
    decoded_json_data = decoded_bytes.decode()
    original_data = json.loads(decoded_json_data)
    return original_data

class GoogleJsonStyle:
    def __init__(self, parent, data, msg=None):
        self.parent = parent
        self.data = data or {}
        if msg:
            self.data["message"] = msg
        if "Items" in self.data:
            self.data["items"] = self.data.pop("Items")

    @staticmethod
    def add_count(data):
        for k in dict(data):
            if k.lower().endswith("count"):
                del data[k]
        if "items" in data:
            data["currentItemCount"] = len(data["items"])
        return data

    @staticmethod
    def add_self(data):
        callback = request.args.get("callback", "")
        self_link = iri_to_uri(request.url)
        self_link = self_link.replace("?callback=" + callback, "")
        self_link = self_link.replace("&callback=" + callback, "")
        data["selfLink"] = self_link
        return data

    @staticmethod
    def add_next_link(data):
        if "items" in data:
            if "last_key" in data:
                start_key = encode_json(data.pop("last_key"))
                next_link = iri_to_uri(request.url)
                if "?" in next_link:
                    next_link += "&start_key=" + start_key
                else:
                    next_link += "?start_key=" + start_key
                data["nextLink"] =  next_link
                data["startKey"] = start_key
        return data

    @staticmethod
    def content_type():
        if request.args.get("callback") and request.method == "GET":
            return "application/javascript"
        else:
            return "application/json"

    def status_code(self):
        data = bool(self.data)
        codes = {
            True: {"POST": 201, "OTHER": 200},
            False: {"POST": 201, "GET": 404, "OTHER": 204},
        }
        return codes.get(data).get(request.method, codes[data]["OTHER"])

    def add_edit_self(self, data):
        if (
            hasattr(self.parent, "put")
            or hasattr(self.parent, "delete")
            or hasattr(self.parent, "patch")
        ):
            data["editLink"] = request.base_url
        return data

    def body(self):
        if not self.data:
            return ""
        body = self.add_count(self.data)
        body = self.add_self(body)
        body = self.add_edit_self(body)
        body = self.add_next_link(body)
        body = OrderedDict(body)
        if "items" in body:
            body["items"] = body.pop("items")
        body = dumps({"data": body}, indent=3)
        if request.args.get("callback") and request.method == "GET":
            body = "{}({});".format(request.args.get("callback"), body)
        return body
