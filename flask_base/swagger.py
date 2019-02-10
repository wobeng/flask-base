from collections import Mapping
from copy import deepcopy

import simplejson
import yaml
from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin

from flask_base.utils import function_args, http_path, find_schemas, http_methods

mm_plugin = MarshmallowPlugin()
flask_plugin = FlaskPlugin()

api_spec = APISpec(
    title='',
    version='1.0.0',
    openapi_version='2.0',
    plugins=(mm_plugin, flask_plugin)
)


def generate_swagger(cls):
    def update_nested(orig_dict, new_dict):
        """Update nested dictionary"""
        for key, value in new_dict.items():
            if isinstance(value, Mapping):
                tmp = update_nested(orig_dict.get(key, {}), value)
                orig_dict[key] = tmp
            elif isinstance(value, list):
                orig_dict[key] = (orig_dict.get(key, []) + value)
            else:
                orig_dict[key] = new_dict[key]
        return orig_dict

    def generate_spec(schema):
        """Generate apispec """
        new_spec = deepcopy(api_spec)
        new_spec.info['title'] = class_name
        new_spec.info['version'] = '1.0.0'
        new_spec.definition(class_name, schema=schema)
        return simplejson.loads(simplejson.dumps(new_spec.to_dict()['definitions']))

    def find_specs(schemas):
        """Generate apispec for parent and child schema"""
        schemas_data = {}
        for schema in schemas:
            data = generate_spec(schema)
            schemas_data = update_nested(schemas_data, data)
        return schemas_data

    for http_method in [attr for attr in dir(cls) if attr in http_methods]:
        view_func = getattr(cls, http_method)
        class_name = cls.__name__ + '.' + http_method.title()

        """For each incoming data given, generate"""
        definitions = {}
        parameters = []
        tags = getattr(cls, 'tags', [])

        view_func_args = function_args(view_func)

        # add global arg if global args exist in class
        if hasattr(cls, 'global_args'):
            for arg in cls.global_args:
                if arg not in view_func_args:
                    view_func_args[arg] = cls.global_args[arg]
                    view_func_args[arg]['scope'] = 'global'

        for arg, val in {arg: val for arg, val in view_func_args.items() if arg in http_path}.items():
            spec = find_specs(find_schemas(http_method.title(), arg, cls.schema))
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
            elif arg in ['view_arg', 'header', 'query']:
                for f, v in spec[class_name]['properties'].items():
                    parameter = dict(name=f, required=False)
                    parameter['in'] = ('path' if arg == 'view_arg' else arg)
                    parameter['type'] = v['type']
                    if 'required' in spec[class_name] and f in spec[class_name]['required']:
                        parameter['required'] = True
                    if 'example' in spec[class_name]['properties'][f]:
                        parameter['default'] = spec[class_name]['properties'][f]['example']
                    parameters.append(parameter)

        output = list([class_name, class_name, '---'])
        if view_func.__doc__:
            output[1] = view_func.__doc__
        output.append(yaml.safe_dump({'tags': tags}, allow_unicode=True, default_flow_style=False))
        output.append(yaml.safe_dump({'parameters': parameters}, allow_unicode=True, default_flow_style=False))
        if definitions:
            output.append(yaml.safe_dump({'definitions': definitions}, allow_unicode=True, default_flow_style=False))

        setattr(getattr(cls, http_method), '__doc__', '\n'.join(output))

    return cls
