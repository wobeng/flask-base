import os
import re
from urllib.parse import parse_qs

import bcrypt
import dateutil.parser
import phonenumbers
import requests
import validators
from dateutil.rrule import rrulestr
from jsonschema import Draft7Validator
from marshmallow import fields, validate, INCLUDE
from more_itertools import unique_everseen
from netaddr import IPNetwork
from netaddr.core import AddrFormatError
import socket
from flask_base.jsonstyle import decode_json
from flask_base.swagger import mm_plugin
import traceback
from datetime import datetime, timezone
import pytz

friendly_allowed_chars = [" ", "&", "'", "-", "_", "(", ")", ".", "/"]

FIELD_NULL = "FieldNotNullException", "This field cannot be empty"
FIELD_VALIDATOR_FAILED = (
    "FieldValidatorFailedException",
    "This field is invalid",
)
FIELD_REQUIRED = "FieldRequiredException", "This field is required"
FIELD_FIELD_TYPE = "FieldTypeException", "This field is invalid"
FIELD_INVALID = "FieldValidatorFailedException", "This field is invalid"
FIELD_MAX_LENGTH = (
    "FieldMaxLengthException",
    "This field is too long or higher than expected",
)
FIELD_MIN_LENGTH = (
    "FieldMinLengthException",
    "This field is too short or lower than expected",
)
FIELD_TAG = (
    "FieldTagTypeException",
    "This field is invalid. Only alphanumeric and dash are allowed",
)
FIELD_UNIQUE_TAG = (
    "FieldTagUniqueTypeException",
    "This field is invalid. Only alphanumeric, dash, and forward slash are allowed",
)
FIELD_SPACE_TAG = (
    "FieldTagSpaceTypeException",
    "This field is invalid. Only alphanumeric, dash and space are allowed",
)

FIELD_FRIENDLY_NAME = (
    "FieldFriendlyNameTypeException",
    "This field is invalid. Only alphanumeric, space and special symbols {} are allowed".format(
        " ".join(friendly_allowed_chars)
    ),
)
FIELD_RECAPTCHA = (
    "FieldRecaptchaTypeException",
    "Are you human? Refresh page and submit again",
)
FIELD_PASSWORD = (
    "FieldPasswordTypeException",
    "Password must be at least 8 characters in length. Must contain a lowercase, uppercase and number.",
)
FIELD_PHONE = (
    "FieldPhoneTypeException",
    "Phone is invalid. Example: +12035556677.",
)
FIELD_CIDR = (
    "FieldCidrTypeException",
    "Address block is invalid. Example: 8.8.8.8/32 for IPv4 or 2001:4860:4860::8888/32 for IPv6",
)
FIELD_RRULE = (
    "FieldRruleTypeException",
    "Rrule is invalid. Example: FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1",
)
FIELD_JSONSCHEMA = (
    "FieldJsonSchemaTypeException",
    "Schema is invalid. Example: http://json-schema.org/examples.html",
)
FIELD_DATE = "FieldDateTypeException", "Date is invalid. Example: mm/dd/yyyy."
FIELD_DATETIME = (
    "FieldDateTimeTypeException",
    "Datetime is invalid. Example: mm/dd/yyyy-00:00:00.",
)
FIELD_FUTURE_DATETIME = (
    "FieldFutureDateTimeTypeException",
    "Future datetime is invalid. Datetime should be greater than today's datetime.",
)
FIELD_START_END_DATE = (
    "FieldStartEndDateException",
    "Start date is invalid. Example: mm/dd/yyyy.",
)
FIELD_START_END_DATETIME = (
    "FieldStartEndDateException",
    "Start date is invalid. Example: mm/dd/yyyy-00:00:00.",
)
FIELD_DOMAIN = (
    "FieldDomainTypeException",
    "Domain is invalid. Example: example.com",
)
FIELD_EMAIL = (
    "FieldEmailTypeException",
    "Email is invalid. Example: username@example.com.",
)
FIELD_URL = (
    "FieldUrlTypeException",
    "Url is invalid. Example: http://example.com",
)
FIELD_USERNAME = (
    "FieldUsernameTypeException",
    "Username is invalid. Example: username@example.com or +12035556677.",
)


def find_replace_all(str, replace_str, allowed_chars):
    for item in allowed_chars:
        str = str.replace(item, replace_str)
    return str


def error_msg(field):
    if os.environ.get("MMALLOW_ERROR_EXPAND", "true") == "true":
        return field[1]
    return field[0]


def validate_email(value, min_length=None):
    if not min_length and value == "":
        return value
    value = value.replace(" ", "").strip()
    if "@" not in value or "." not in value:
        return
    if validators.email(value) is not True:
        return
    return value


def validate_phone(value, min_length=None):
    if not min_length and value == "":
        return value
    try:
        input_number = phonenumbers.parse(value)
        if not (phonenumbers.is_valid_number(input_number)):
            return
        return phonenumbers.format_number(
            input_number, phonenumbers.PhoneNumberFormat.E164
        )
    except BaseException:
        return


def validate_username(value, min_length=None):
    if "@" in value and "." in value:
        return validate_email(value, min_length), "email"
    elif value[1].isdigit():
        if value[0] != "+":
            value = "+" + value
        return validate_phone(value, min_length), "phone"
    return None, None


def date_time(
    self,
    value,
    attr,
    obj,
    validator_failed,
    date=False,
    iso_format=False,
    timezone_func=None,
):
    if not self.min_length and value == "":
        return value

    try:
        # get timezone
        timezone_str = timezone_func() if timezone_func else "UTC"
        dt = parse_and_localize(value, timezone_str)
        if date:
            dt = dt.date()

        if attr and (attr.startswith("start_") or attr.startswith("end_")):
            start_date, end_date = validate_duration(
                dt,
                attr,
                obj,
                date,
                timezone_str,
            )
            if start_date > end_date:
                self.error_messages["validator_failed"] = validator_failed
                raise BaseException

        return dt.isoformat() if iso_format else dt

    except BaseException:
        traceback.print_exc()
        raise self.make_error("validator_failed")


def parse_and_localize(value, timezone_str):
    dt = dateutil.parser.parse(value).replace(microsecond=0)

    if dt.tzinfo is None:
        timezone = pytz.timezone(timezone_str)
        dt = timezone.localize(dt)

    return dt.astimezone(pytz.utc)


def validate_duration(dt, attr, obj, date, timezone_str):
    duration = {attr: dt}

    if attr.startswith("start_"):
        start_key = attr
        end_key = "end_" + attr[6:]
        other_date_key = end_key
    else:
        end_key = attr
        start_key = "start_" + attr[4:]
        other_date_key = start_key

    other_dt = parse_and_localize(obj[other_date_key], timezone_str)

    if date:
        other_dt = other_dt.date()

    duration[other_date_key] = other_dt

    start_dt = duration.get(start_key, duration.get(end_key))
    end_dt = duration.get(end_key, duration.get(start_key))

    return start_dt, end_dt


def default_error_messages():
    return dict(
        {
            "null": error_msg(FIELD_NULL),
            "validator_failed": error_msg(FIELD_VALIDATOR_FAILED),
            "required": error_msg(FIELD_REQUIRED),
            "field_type": error_msg(FIELD_FIELD_TYPE),
            "invalid": error_msg(FIELD_INVALID),
            "max_length": error_msg(FIELD_MAX_LENGTH),
            "min_length": error_msg(FIELD_MIN_LENGTH),
        }
    )


class Fields:
    def _serialize(self, value, attr, obj, **kwargs):
        for method in [
            "main_deserialize",
            "post_deserialize",
        ]:
            method = getattr(self, method, None)
            if method:
                value = method(value, attr, obj, **kwargs)

        if self.post_validate:
            try:
                value = self.post_validate(value)
            except BaseException:
                error = self.make_error("validator_failed")
                error.messages.append(traceback.format_exc())
                raise error
        return value

    def _deserialize(self, value, attr, obj, **kwargs):
        for method in [
            "main_deserialize",
            "post_deserialize",
        ]:
            method = getattr(self, method, None)
            if method:
                value = method(value, attr, obj, **kwargs)

        # exit if field is allowed to be falsy
        if (
            getattr(self, "min_length", 1) == 0
            or getattr(self, "allow_empty", 1) is True
        ):
            return value

        if self.post_validate:
            try:
                value = self.post_validate(value)
                if not value:
                    raise
            except BaseException:
                error = self.make_error("validator_failed")
                error.messages.append(traceback.format_exc())
                raise error

        return value


class String(Fields, fields.String):
    def __init__(
        self,
        min_length=1,
        max_length=20000,
        friendly_name=False,
        allow_chars=None,
        lower=False,
        capitalize=False,
        post_validate=None,
        *args,
        **kwargs,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.friendly_name = friendly_name
        self.lower = lower
        self.capitalize = capitalize
        self.post_validate = post_validate
        self.allow_chars = allow_chars or friendly_allowed_chars
        kwargs.setdefault("error_messages", default_error_messages())
        super(String, self).__init__(*args, **kwargs)
        self.error_messages["friendly_name_validator_failed"] = error_msg(
            FIELD_FRIENDLY_NAME
        )

    def main_deserialize(self, value, attr, obj, **kwargs):
        value = str(value).strip()
        if len(value) < self.min_length:
            raise self.make_error("min_length")
        if len(value) > self.max_length:
            raise self.make_error("max_length")
        if self.lower:
            value = value.lower()
        if self.capitalize:
            value = value.capitalize()
        if (
            self.friendly_name
            and not find_replace_all(value, "", self.allow_chars).isalnum()
        ):
            raise self.make_error("friendly_name_validator_failed")
        return fields.String._deserialize(self, value, attr, obj, **kwargs)


class StringTag(String):
    def __init__(self, *args, **kwargs):
        allow_chars = ["-"]
        super(StringTag, self).__init__(
            *args, **kwargs, friendly_name=True, allow_chars=allow_chars
        )
        self.error_messages["friendly_name_validator_failed"] = error_msg(FIELD_TAG)


class StringUniqueTag(String):
    def __init__(self, *args, **kwargs):
        allow_chars = ["/", "-"]
        super(StringUniqueTag, self).__init__(
            *args, **kwargs, lower=True, friendly_name=True, allow_chars=allow_chars
        )
        self.error_messages["friendly_name_validator_failed"] = error_msg(
            FIELD_UNIQUE_TAG
        )


class StringSpaceTag(String):
    def __init__(self, *args, **kwargs):
        allow_chars = [" ", "-"]
        super(StringSpaceTag, self).__init__(
            *args, **kwargs, friendly_name=True, allow_chars=allow_chars
        )
        self.error_messages["friendly_name_validator_failed"] = error_msg(
            FIELD_SPACE_TAG
        )


class Recaptcha(String):
    def __init__(self, action, *args, **kwargs):
        self.action = action
        kwargs.setdefault("error_messages", default_error_messages())
        super(Recaptcha, self).__init__(*args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_RECAPTCHA)

    def post_deserialize(self, value, attr, obj, **kwargs):
        if value == os.environ["RECAPTCHA_SECRET_TEST"]:
            return True
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": os.environ["RECAPTCHA_SECRET"], "response": value},
        ).json()
        if not r.get("success", False):
            raise self.make_error("validator_failed")
        if r.get("action", "") != self.action:
            raise self.make_error("validator_failed")
        if r.get("score", 0.0) < float(os.environ["RECAPTCHA_SCORE"]):
            raise self.make_error("validator_failed")
        return r["success"]


class Password(String):
    def __init__(self, *args, **kwargs):
        regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
        self.regex = re.compile(regex, 0) if isinstance(regex, (str, bytes)) else regex
        super(Password, self).__init__(*args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_PASSWORD)

    def post_deserialize(self, value, attr, obj, **kwargs):
        if self.regex.match(value) is None:
            raise self.make_error("validator_failed")
        return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode()


mm_plugin.map_to_openapi_type(Password, "string", "password")


class Cidr(String):
    def __init__(self, *args, **kwargs):
        super(Cidr, self).__init__(lower=True, *args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_CIDR)

    def post_deserialize(self, value, attr, obj, **kwargs):
        try:
            IPNetwork(value)
            return value
        except AddrFormatError:
            raise self.make_error("validator_failed")


class Phone(String):
    def __init__(self, *args, **kwargs):
        super(Phone, self).__init__(lower=True, *args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_PHONE)

    def post_deserialize(self, value, attr, obj, **kwargs):
        output = validate_phone(value, self.min_length)
        if not output:
            raise self.make_error("validator_failed")
        return output


class Rrule(String):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("metadata", {"example": "FREQ=DAILY"})
        super(Rrule, self).__init__(*args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_RRULE)

    def post_deserialize(self, value, attr, obj, **kwargs):
        value = value.replace("SECONDLY", "HOURLY").replace("MINUTELY", "HOURLY")
        try:
            rrulestr(value)
            return value
        except BaseException:
            raise self.make_error("validator_failed")


class ParseQueryString(String):
    def post_deserialize(self, value, attr, obj, **kwargs):
        try:
            r = parse_qs(attr + "=" + value, strict_parsing=True)
            output = decode_json(r[attr][0])
            if not isinstance(output, dict):
                raise
            return output
        except BaseException:
            raise self.make_error("validator_failed")


class Date(String):
    def __init__(self, iso_format=True, *args, **kwargs):
        super(Date, self).__init__(*args, **kwargs)
        self.iso_format = iso_format

    def post_deserialize(self, value, attr, obj, **kwargs):
        self.error_messages["validator_failed"] = error_msg(FIELD_DATE)
        return date_time(
            self,
            value,
            attr,
            obj,
            error_msg(FIELD_START_END_DATE),
            date=True,
            iso_format=self.iso_format,
        )


mm_plugin.map_to_openapi_type(Date, "string", "date")


class DateTime(String):
    def __init__(self, iso_format=False, timezone_func=None, *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)
        self.iso_format = iso_format
        self.timezone_func = timezone_func

    def post_deserialize(self, value, attr, obj, **kwargs):
        self.error_messages["validator_failed"] = error_msg(FIELD_DATETIME)
        return date_time(
            self,
            value,
            attr,
            obj,
            error_msg(FIELD_START_END_DATETIME),
            iso_format=self.iso_format,
            timezone_func=self.timezone_func,
        )


mm_plugin.map_to_openapi_type(DateTime, "string", "date-time")


class Domain(String):
    def __init__(self, *args, **kwargs):
        super(Domain, self).__init__(lower=True, *args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_DOMAIN)

    def post_deserialize(self, value, attr, obj, **kwargs):
        if not self.min_length and value == "":
            return value
        if not validators.domain(value):
            raise self.make_error("validator_failed")
        try:
            socket.gethostbyname(value)
        except socket.gaierror:
            raise self.make_error("validator_failed")
        return value


mm_plugin.map_to_openapi_type(Domain, "string", "domain")


class Email(String):
    def __init__(self, *args, **kwargs):
        super(Email, self).__init__(lower=True, *args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_EMAIL)

    def post_deserialize(self, value, attr, obj, **kwargs):
        output = validate_email(value, min_length=None)
        if not output:
            raise self.make_error("validator_failed")
        return output


mm_plugin.map_to_openapi_type(Email, "string", "email")


class Url(String):
    def __init__(self, *args, **kwargs):
        super(Url, self).__init__(lower=True, *args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_URL)

    def post_deserialize(self, value, attr, obj, **kwargs):
        if not self.min_length and value == "":
            return value
        if not validators.url(value):
            raise self.make_error("validator_failed")
        return value


mm_plugin.map_to_openapi_type(Url, "string", "url")


class Dict(Fields, fields.Dict):
    def __init__(self, allow_empty=False, post_validate=None, *args, **kwargs):
        self.allow_empty = allow_empty
        self.post_validate = post_validate
        kwargs.setdefault("error_messages", default_error_messages())
        super(Dict, self).__init__(*args, **kwargs)

    def main_deserialize(self, value, attr, data, **kwargs):
        if self.allow_empty and not value:
            return value
        if not value:
            raise self.make_error("validator_failed")
        return fields.Dict._deserialize(self, value, attr, data)


mm_plugin.map_to_openapi_type(Dict, "object", None)


class JsonSchema(Dict):
    def __init__(self, *args, **kwargs):
        super(JsonSchema, self).__init__(*args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_JSONSCHEMA)

    def post_deserialize(self, value, attr, obj, **kwargs):
        try:
            for i in list(value.values()):
                if not i:
                    raise BaseException
            value["$schema"] = "http://json-schema.org/schema#"
            Draft7Validator.check_schema(value)
            return value
        except BaseException:
            raise self.make_error("validator_failed")


class Username(String):
    def __init__(self, *args, **kwargs):
        super(Username, self).__init__(lower=True, *args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_USERNAME)

    def post_deserialize(self, value, attr, obj, **kwargs):
        output, output_type = validate_username(value, self.min_length)

        if output_type == "email":
            self.error_messages["validator_failed"] = error_msg(FIELD_EMAIL)
        elif output_type == "phone":
            self.error_messages["validator_failed"] = error_msg(FIELD_PHONE)

        if not output:
            raise self.make_error("validator_failed")

        return output


class List(Fields, fields.List):
    def __init__(
        self,
        cls_or_instance,
        min_length=1,
        max_length=20000,
        post_validate=None,
        duplicate_callable=None,
        remove_duplicates=False,
        **kwargs,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.post_validate = post_validate
        self.duplicate_callable = duplicate_callable
        self.remove_duplicates = remove_duplicates
        kwargs.setdefault("error_messages", default_error_messages())
        super(List, self).__init__(cls_or_instance, **kwargs)

    def _validate(self, value):
        if self.min_length == 0 and not value:
            return None
        return super(List, self)._validate(value)

    def main_deserialize(self, value, attr, data, **kwargs):
        if len(value) < self.min_length:
            raise self.make_error("required")
        if len(value) > self.max_length:
            raise self.make_error("max_length")
        if isinstance(value, str):
            value = value.split(",")

        value = list(value)

        if self.remove_duplicates:
            value = list(unique_everseen(value, key=self.duplicate_callable))

        return fields.List._deserialize(self, value, attr, data, **kwargs)

    def post_deserialize(self, value, attr, data, **kwargs):
        if self.min_length == 0 and not value:
            return None
        return value


mm_plugin.map_to_openapi_type(List, "array", None)


class Set(List):
    def __init__(self, cls_or_instance, min_length=1, max_length=20000, **kwargs):
        super(Set, self).__init__(
            cls_or_instance, True, min_length, max_length, **kwargs
        )

    def post_deserialize(self, value, attr, data, **kwargs):
        if not value:
            return None
        return value


mm_plugin.map_to_openapi_type(Set, "array", None)


class Boolean(fields.Boolean):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_messages", default_error_messages())
        super(Boolean, self).__init__(*args, **kwargs)


mm_plugin.map_to_openapi_type(Boolean, "boolean", None)


class Integer(Fields, fields.Integer):
    def __init__(
        self, min_length=None, max_length=None, post_validate=None, *args, **kwargs
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.post_validate = post_validate
        kwargs.setdefault("error_messages", default_error_messages())
        super(Integer, self).__init__(*args, **kwargs)

    def main_deserialize(self, value, attr, obj, **kwargs):
        if self.min_length is not None:
            if self.min_length and value < self.min_length:
                raise self.make_error("min_length")
        if self.max_length is not None:
            if self.max_length and value > self.max_length:
                raise self.make_error("max_length")
        return fields.Integer._deserialize(self, value, attr, obj, **kwargs)


mm_plugin.map_to_openapi_type(Integer, "integer", "int32")


class FutureTimestamp(Integer):
    def __init__(self, *args, **kwargs):
        super(FutureTimestamp, self).__init__(*args, **kwargs)
        self.error_messages["validator_failed"] = error_msg(FIELD_FUTURE_DATETIME)

    def post_deserialize(self, value, attr, obj, **kwargs):
        present = int(datetime.now(timezone.utc).timestamp())
        if present >= value:
            raise self.make_error("validator_failed")
        return value


mm_plugin.map_to_openapi_type(FutureTimestamp, "integer", "int32")


class Float(fields.Float):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_messages", default_error_messages())
        super(Float, self).__init__(*args, **kwargs)


mm_plugin.map_to_openapi_type(Float, "number", "float")


class Nested(Fields, fields.Nested):
    def __init__(self, *args, post_validate=None, allow_empty=False, **kwargs):
        self.post_validate = post_validate
        self.allow_empty = allow_empty
        kwargs.setdefault("error_messages", default_error_messages())
        super(Nested, self).__init__(*args, **kwargs)

    def main_deserialize(self, value, attr, obj, **kwargs):
        if self.allow_empty and not value:
            return value
        return fields.Nested._deserialize(self, value, attr, obj, **kwargs)


class OneOf(validate.OneOf):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error", error_msg(FIELD_VALIDATOR_FAILED))
        super(OneOf, self).__init__(*args, **kwargs)


class ContainsOnly(validate.ContainsOnly):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error", error_msg(FIELD_VALIDATOR_FAILED))
        super(ContainsOnly, self).__init__(*args, **kwargs)


class Function(fields.Field):
    def __init__(
        self,
        serialize=None,
        deserialize=None,
        input_type=None,
        func_kwargs=None,
        allow_empty=False,
        *args,
        **kwargs,
    ):
        self.func_kwargs = func_kwargs or dict()
        self.serialize_func = serialize
        self.deserialize_func = deserialize
        self.input_type = input_type or str
        self.allow_empty = allow_empty
        kwargs.setdefault("error_messages", default_error_messages())
        super(Function, self).__init__(*args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, self.input_type):
            raise self.make_error("validator_failed")
        if self.allow_empty and not value:
            return value
        try:
            data = self.deserialize_func(value, **self.func_kwargs)
            if data:
                return data
        except BaseException:
            pass
        raise self.make_error("validator_failed")


class StringFunction(Function):
    def __init__(self, *args, **kwargs):
        super(StringFunction, self).__init__(input_type=str, *args, **kwargs)


mm_plugin.map_to_openapi_type(StringFunction, "string", None)


class DictFunction(Function):
    def __init__(self, *args, **kwargs):
        super(DictFunction, self).__init__(input_type=dict, *args, **kwargs)


mm_plugin.map_to_openapi_type(DictFunction, "object", None)


class NestFunction(Nested):
    def __init__(self, nested, serialize=None, deserialize=None, *args, **kwargs):
        self.serialize_func = serialize
        self.deserialize_func = deserialize
        super(NestFunction, self).__init__(nested, *args, **kwargs)

    def _deserialize(self, value, attr, obj, **kwargs):
        validated_data = super(NestFunction, self)._deserialize(value, attr, obj)
        post_validated_data = self.deserialize_func(validated_data)
        if not post_validated_data:
            raise self.make_error("validator_failed")
        return post_validated_data


class DynamicNested(Nested):
    def __init__(self, nested, key_type, *args, **kwargs):
        super(DynamicNested, self).__init__(nested, unknown=INCLUDE, *args, **kwargs)
        self.key_type = key_type
        self.nested_schema = Nested(nested, unknown=INCLUDE)

    def post_deserialize(self, value, attr, obj, **kwargs):
        ret = {}
        for key, val in value.items():
            k = self.key_type.deserialize(key, key, obj)
            v = self.nested_schema.deserialize(val, key, obj)
            ret[k] = v
        return ret

    def post_serialize(self, value, attr, obj, **kwargs):
        ret = {}
        for key, val in value.items():
            k = self.key_type._serialize(key, attr, obj)
            v = self.nested_schema.serialize(key, self.get_value(attr, obj))
            ret[k] = v
        return ret
