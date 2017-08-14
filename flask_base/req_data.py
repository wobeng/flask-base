from flask import request


def single_or_many(data, many=False):
    if many:
        if data:
            if not isinstance(data, list):
                return [data]
            return data
        return []
    return data


def multi_dict_marsh(multi_dict, many=False):
    print(multi_dict,many)
    response = []
    # get max range
    try:
        max_dict = max([len(multi_dict.getlist(k)) for k in list(multi_dict.keys())])
    except ValueError:
        max_dict = 0
    # convert multi dict to marshmallow format
    for i in range(max_dict):
        d = {}
        for k in list(multi_dict.keys()):
            try:
                d[k] = multi_dict.getlist(k)[i]
            except IndexError:
                pass
        response.append(d)

    if many and response:
        return response
    if not many and response:
        return response[0]
    return [] if many else {}


def request_body(many=False):
    body = request.get_json(True, True)
    if not body:
        return multi_dict_marsh(request.form, many)
    return single_or_many(body, many)


def request_query(many=False):
    args = multi_dict_marsh(request.args, many)
    return single_or_many(args, many)


def request_header(many=False):
    headers = {
        key.lower().replace('-', '_'): val
        for key, val in request.headers
    }
    return single_or_many(headers, many)


def request_view_arg(many=False):
    args = dict(request.view_args)
    return single_or_many(args, many)
