import json
import re
import time
import datetime

import openglider.config
from openglider.jsonify.migration import Migration
from openglider.utils import recursive_getattr

__ALL__ = ['dumps', 'dump', 'loads', 'load']

# Main json-export routine.
# Maybe at some point it can become necessary to de-reference classes with _module also,
# because of same-name-elements....
# For the time given, we're alright
datetime_format = "%d.%m.%Y %H:%M"
datetime_format_regex = re.compile(r'^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$')

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if obj.__class__.__module__ == 'numpy':
            return obj.tolist()
        elif isinstance(obj, datetime.datetime):
            return obj.strftime(datetime_format)
        elif hasattr(obj, "__json__"):
            result = obj.__json__()

            if type(result) == dict:
                type_str = str(obj.__class__)
                module = obj.__class__.__module__
                type_regex = "<class '{}\.(.*)'>".format(module.replace(".", "\."))
                class_name = re.match(type_regex, type_str).group(1)

                return {"_type": class_name,
                        "_module": module,
                        "data": obj.__json__()}
            else:
                return result
        else:
            return super(Encoder, self).default(obj)


def get_element(_module, _name):
    for rex in openglider.config["json_forbidden_modules"]:
        if re.match(rex, _module):
            raise Exception
        elif re.match(rex, _name):
            raise Exception
    for rex in openglider.config["json_allowed_modules"]:
        match = re.match(rex, _module)
        if match:
            fromlist = [str(w) for w in _module.split(".")]
            module = __import__(_module, fromlist=fromlist)
            obj = recursive_getattr(module, _name)
            return obj


def object_hook(dct):
    """
    Return the de-serialized object
    """
    for key, value in dct.items():
        if isinstance(value, str) and datetime_format_regex.match(value):
            dct[key] = datetime.datetime.strptime(value, datetime_format)
            
    if '_type' in dct and '_module' in dct:
        obj = get_element(dct["_module"], dct["_type"])

        try:
            # use the __from_json__ function if present. __init__ otherwise
            deserializer = getattr(obj, '__from_json__', None)
            if deserializer is None:
                deserializer = obj
            return deserializer(**dct['data'])
        except TypeError as e:
            raise TypeError("{} in element: {} ({})".format(e, obj, dct["_module"]))

    else:
        return dct


def add_metadata(data):
    if isinstance(data, dict) and 'MetaData' in data:
        data['MetaData']['date_modified'] = time.strftime("%d.%m.%y %H:%M")
        return data
    else:
        return {'MetaData': {'application': 'openglider',
                             'version': openglider.__version__,
                             'author': openglider.config["user"],
                             'date_created': time.strftime("%d.%m.%y %H:%M"),
                             'date_modified': time.strftime("%d.%m.%y %H:%M")},
                'data': data}


def dumps(obj, add_meta=True):
    if add_meta:
        obj = add_metadata(obj)
    return json.dumps(obj, cls=Encoder)


def dump(obj, fp, add_meta=True):
    if add_meta:
        obj = add_metadata(obj)
    return json.dump(obj, fp, cls=Encoder, indent=4)


def loads(obj):
    raw_data = json.loads(obj)
    miigration = Migration(raw_data)
    if miigration.required:
        return json.loads(miigration.migrate(), object_hook=object_hook)

    return json.loads(obj, object_hook=object_hook)


def load(fp):
    raw_data = json.load(fp)
    miigration = Migration(raw_data)
    if miigration.required:
        return json.loads(miigration.migrate(), object_hook=object_hook)

    return json.load(fp, object_hook=object_hook)