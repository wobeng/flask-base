import os
import re
from datetime import datetime
from urllib.parse import parse_qs

import bcrypt
import dateutil.parser
import phonenumbers
import requests
import simplejson
import validators
from dateutil.rrule import rrulestr
from jsonschema import Draft7Validator
from marshmallow import fields, validate
from more_itertools import unique_everseen
from pytz import UTC
from validate_email import validate_email

from flask_base.swagger import mm_plugin


def datetime_utc(dt=None):
    if not dt:
        dt = datetime.utcnow()
    return dt.replace(tzinfo=UTC)


def default_error_messages(null=None, validator_failed=None, required=None,
                           field_type=None, invalid=None, max_length=None):
    return dict({
        'null': null or 'FieldNotNullException',
        'validator_failed': validator_failed or 'FieldValidatorFailedException',
        'required': required or 'FieldRequiredException',
        'field_type': field_type or 'FieldTypeException',
        'invalid': invalid or 'FieldValidatorFailedException',
        'max_length': max_length or 'FieldMaxLengthException'
    })


class String(fields.String):
    def __init__(self, min_length=1, max_length=5000, replace_space=False, *args, **kwargs):
        self.min_length = min_length
        self.max_length = max_length
        self.replace_space = replace_space
        kwargs.setdefault('error_messages', default_error_messages())
        super(String, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        if len(value) < self.min_length:
            self.fail('required')
        if len(value) > self.max_length:
            self.fail('max_length')
        return value.replace(' ', '-') if self.replace_space else value


class Recaptcha(fields.String):
    def __init__(self, action, *args, **kwargs):
        self.action = action
        kwargs.setdefault('error_messages', default_error_messages())
        super(Recaptcha, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(Recaptcha, self)._deserialize(value, attr, obj)
        if os.environ['ENVIRONMENT'] == 'develop' and value == os.environ['RECAPTCHA_TEST_VALUE']:
            return True
        r = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={'secret': os.environ['RECAPTCHA_SECRET'], 'response': value}
        ).json()
        if not r.get('success', False):
            self.fail('validator_failed')
        if r.get('action', '') != self.action:
            self.fail('validator_failed')
        if r.get('score', 0.0) < float(os.environ['RECAPTCHA_SCORE']):
            self.fail('validator_failed')
        return r['success']


@mm_plugin.map_to_openapi_type('string', '	password')
class Password(String):
    def __init__(self, *args, **kwargs):
        regex = '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
        self.regex = re.compile(regex, 0) if isinstance(regex, (str, bytes)) else regex
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldPasswordTypeException'))
        super(Password, self).__init__(min_length=8, *args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(Password, self)._deserialize(value, attr, obj)
        if self.regex.match(value) is None:
            self.fail('validator_failed')
        return bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode()


class Phone(String):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldPhoneTypeException'))
        super(Phone, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(Phone, self)._deserialize(value, attr, obj)
        if not self.min_length and value == '':
            return value
        try:
            input_number = phonenumbers.parse(value)
            if not (phonenumbers.is_valid_number(input_number)):
                self.fail('validator_failed')
            return phonenumbers.format_number(input_number, phonenumbers.PhoneNumberFormat.E164)
        except BaseException:
            self.fail('validator_failed')


class Rrule(String):
    def __init__(self, allow_none=True, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldRruleTypeException'))
        kwargs.setdefault('example', 'FREQ=DAILY')
        super(Rrule, self).__init__(allow_none=allow_none, *args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        if self.allow_none and value is None:
            return value
        value = super(Rrule, self)._deserialize(value, attr, obj)
        try:
            rrulestr(value)
            return value
        except BaseException:
            self.fail('validator_failed')


class ParseQueryString(String):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages())
        super(ParseQueryString, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(ParseQueryString, self)._deserialize(value, attr, obj)
        try:
            r = parse_qs(attr + '=' + value, strict_parsing=True)
            return simplejson.loads(r[attr][0])
        except BaseException:
            self.fail('validator_failed')


class JsonSchema(fields.Dict):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldJsonSchemaTypeException'))
        super(JsonSchema, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(JsonSchema, self)._deserialize(value, attr, obj)
        try:
            if not value:
                raise BaseException
            value['$schema'] = 'http://json-schema.org/schema#'
            Draft7Validator.check_schema(value)
            return simplejson.dumps(value)
        except BaseException:
            self.fail('validator_failed')


def _date_time(self, value, attr, obj, validator_failed, date=False):
    if not self.min_length and value == '':
        return value
    try:
        # convert to datetime
        dt = dateutil.parser.parse(value).replace(microsecond=0)
        if date:
            dt = dt.date()
        # compare start and end date if its duration
        attr = attr or ''
        if attr and attr.startswith('start_') or attr.startswith('end_'):
            # set dates
            duration = dict()
            duration[attr] = dt
            other_date = 'end_date' if attr.startswith('start_') else 'start_date'
            duration[other_date] = dateutil.parser.parse(obj[other_date])
            if date:
                duration[other_date] = duration[other_date].date()
            # get dates
            start_date = duration.get('start_date', duration.get('end_date'))
            end_date = duration.get('end_date', duration.get('start_date'))
            # compare dates
            if start_date > end_date:
                self.error_messages['validator_failed'] = validator_failed
                raise BaseException
        # return string if preferred
        if self.output_string:
            return dt.isoformat()
        return dt
    except BaseException:
        self.fail('validator_failed')


@mm_plugin.map_to_openapi_type('string', 'date')
class Date(String):
    def __init__(self, output_string=False, *args, **kwargs):
        self.output_string = output_string
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldDateTypeException'))
        super(Date, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(Date, self)._deserialize(value, attr, obj)
        return _date_time(self, value, attr, obj, 'StartEndDateException', date=True)


@mm_plugin.map_to_openapi_type('string', 'date-time')
class DateTime(String):
    def __init__(self, output_string=False, *args, **kwargs):
        self.output_string = output_string
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldDateTimeTypeException'))
        super(DateTime, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(DateTime, self)._deserialize(value, attr, obj)
        return _date_time(self, value, attr, obj, 'StartEndDateTimeException')


@mm_plugin.map_to_openapi_type('string', 'date-time')
class FutureDateTime(DateTime):
    def __init__(self, *args, **kwargs):
        kwargs['error_messages'] = default_error_messages(validator_failed='FieldFutureDateTimeTypeException')
        self.output_string_override = kwargs['output_string']
        kwargs['output_string'] = False
        super(FutureDateTime, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        future = super(FutureDateTime, self)._deserialize(value, attr, obj)
        present = datetime_utc().replace(microsecond=0)
        if present > future:
            self.fail('validator_failed')
        if self.output_string_override:
            return future.isoformat()
        return future


@mm_plugin.map_to_openapi_type('string', 'email')
class Email(String):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldEmailTypeException'))
        super(Email, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(Email, self)._deserialize(value, attr, obj)
        if not self.min_length and value == '':
            return value
        if not validate_email(value):
            self.fail('validator_failed')
        return value


@mm_plugin.map_to_openapi_type('string', 'url')
class Url(String):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages(validator_failed='FieldUrlTypeException'))
        super(Url, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super(Url, self)._deserialize(value, attr, obj)
        if not self.min_length and value == '':
            return value
        if not validators.url(value):
            self.fail('validator_failed')
        return value


@mm_plugin.map_to_openapi_type('object', None)
class Dict(fields.Dict):
    def __init__(self, allow_empty=False, *args, **kwargs):
        self.allow_empty = allow_empty
        kwargs.setdefault('error_messages', default_error_messages())
        super(Dict, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, dict):
            self.fail('validator_failed')
        if self.allow_empty and not value:
            return value
        if not value:
            self.fail('validator_failed')
        return super(Dict, self)._deserialize(value, attr, data)


@mm_plugin.map_to_openapi_type('array', None)
class List(fields.List):
    def __init__(self, cls_or_instance, allow_empty=False, remove_duplicates=False, **kwargs):
        self.allow_empty = allow_empty
        self.remove_duplicates = remove_duplicates
        kwargs.setdefault('error_messages', default_error_messages())
        super(List, self).__init__(cls_or_instance, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, list):
            value = value.split(',')
        if not isinstance(value, list):
            self.fail('validator_failed')
        if self.allow_empty and not value:
            return value
        if not value:
            self.fail('validator_failed')
        value = super(List, self)._deserialize(value, attr, data)
        return list(unique_everseen(value)) if self.remove_duplicates else value


@mm_plugin.map_to_openapi_type('integer', 'int32')
class Integer(fields.Integer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages())
        super(Integer, self).__init__(*args, **kwargs)


@mm_plugin.map_to_openapi_type('number', 'float')
class Float(fields.Float):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages())
        super(Float, self).__init__(*args, **kwargs)


class Nested(fields.Nested):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error_messages', default_error_messages())
        super(Nested, self).__init__(*args, **kwargs)


class OneOf(validate.OneOf):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error', 'FieldValidatorFailedException')
        super(OneOf, self).__init__(*args, **kwargs)


class ContainsOnly(validate.ContainsOnly):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('error', 'FieldValidatorFailedException')
        super(ContainsOnly, self).__init__(*args, **kwargs)


class Function(fields.Field):
    def __init__(self, serialize=None, deserialize=None, input_type=None, *args, **kwargs):
        self.serialize_func = serialize
        self.deserialize_func = deserialize
        self.input_type = input_type or str
        kwargs.setdefault('error_messages', default_error_messages())
        super(Function, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, self.input_type):
            self.fail('validator_failed')
        data = self.deserialize_func(value)
        if not data:
            self.fail('validator_failed')
        return data


@mm_plugin.map_to_openapi_type('string', None)
class StringFunction(Function):
    def __init__(self, *args, **kwargs):
        super(StringFunction, self).__init__(input_type=str, *args, **kwargs)


@mm_plugin.map_to_openapi_type('array', None)
class ListFunction(Function):
    def __init__(self, *args, **kwargs):
        super(ListFunction, self).__init__(input_type=list, *args, **kwargs)


@mm_plugin.map_to_openapi_type('object', None)
class DictFunction(Function):
    def __init__(self, *args, **kwargs):
        super(DictFunction, self).__init__(input_type=dict, *args, **kwargs)


class NestFunction(Nested):
    def __init__(self, nested, serialize=None, deserialize=None, *args, **kwargs):
        self.serialize_func = serialize
        self.deserialize_func = deserialize
        super(NestFunction, self).__init__(nested, *args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        validated_data = super(NestFunction, self)._deserialize(value, attr, obj)
        post_validated_data = self.deserialize_func(validated_data)
        if not post_validated_data:
            self.fail('validator_failed')
        return post_validated_data