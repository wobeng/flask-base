from collections import Mapping

import simplejson
import yaml
from apispec import APISpec
from flask import request
from flask.views import MethodView

from flask_base.helper import function_args, http_path, find_schemas
from flask_base.schema import SchemaView


def generate_swagger(view_func):
    class_name = view_func.__name__ + '.' + request.method.title()

    def update_nested(d, u):
        """Update nested dictionary"""
        for k, v in u.items():
            if isinstance(v, Mapping):
                r = update_nested(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d

    def generate_spec(schema):
        """Generate apispec """
        spec = APISpec(
            title=class_name,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )
        spec.definition(class_name, schema=schema)
        return simplejson.loads(simplejson.dumps(spec.to_dict()['definitions']))

    def find_specs(schemas):
        """Generate apispec for parent and child schema"""
        schemas_data = {}
        for schema in schemas:
            data = generate_spec(schema)
            schemas_data = update_nested(schemas_data, data)
        return schemas_data

    """For each incoming data given, generate"""
    definitions = {}
    parameters = []
    tags = getattr(view_func.view_class, 'tags', [])

    request_method = getattr(view_func.view_class, request.method.lower())
    view_func_args = function_args(request_method)

    for arg, val in {arg: val for arg, val in view_func_args.items() if arg in http_path}.items():
        spec = find_specs(find_schemas(arg, view_func))
        if arg in ['body']:
            parameter = {
                'name': arg,
                'in': 'body',
                'schema': {
                    '$ref': '#/definitions/' + class_name
                }
            }
            if 'required' in spec[class_name]:
                parameter['required'] = True
            parameters.append(parameter)
            definitions.update(spec)
        elif arg in ['view_arg', 'header', 'path', 'query']:
            for f, v in spec[class_name]['properties'].items():
                parameter = dict(name=f, required=False)
                parameter['in'] = ('path' if arg == 'view_arg' else arg).title()
                parameter['type'] = v['type']
                if 'required' in spec[class_name] and f in spec[class_name]['required']:
                    parameter['required'] = True
                if 'default' in spec[class_name]['properties'][f]:
                    parameter['default'] = spec[class_name]['properties'][f]['default']
                parameters.append(parameter)

    output = list([class_name, class_name, '---'])
    if view_func.__doc__:
        output[1] = view_func.__doc__
    output.append(yaml.safe_dump({'tags': tags}, allow_unicode=True, default_flow_style=False))
    output.append(yaml.safe_dump({'parameters': parameters}, allow_unicode=True, default_flow_style=False))
    if definitions:
        output.append(yaml.safe_dump({'definitions': definitions}, allow_unicode=True, default_flow_style=False))
    return output


class SwaggerView(MethodView):
    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        super_cls = super(SwaggerView, cls)
        view_func = super_cls.as_view(name, *class_args, **class_kwargs)
        view_func.view_class = super_cls
        swagger_output = generate_swagger(view_func)

        view_func.__name__ = name
        view_func.__doc__ = '\n'.join(swagger_output)
        view_func.__module__ = super_cls.__module__
        view_func.methods = super_cls.methods
        return view_func


class SchemaSwaggerView(SchemaView):
    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        super_cls = super(SchemaView, cls)
        view_func = super_cls.as_view(name, *class_args, **class_kwargs)
        view_func.view_class = super_cls
        swagger_output = generate_swagger(view_func)

        view_func.__name__ = name
        view_func.__doc__ = '\n'.join(swagger_output)
        view_func.__module__ = super_cls.__module__
        view_func.methods = super_cls.methods
        return view_func
