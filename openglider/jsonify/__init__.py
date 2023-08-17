from io import TextIOWrapper
import json
import re
import sys
import time
import datetime
from typing import Any, Dict, Type

import pydantic
import openglider.config
from openglider.jsonify.encoder import Encoder
from openglider.jsonify.migration import Migration
from openglider.utils import recursive_getattr

__ALL__ = ['dumps', 'dump', 'loads', 'load']

# Main json-export routine.
# Maybe at some point it can become necessary to de-reference classes with _module also,
# because of same-name-elements....
# For the time given, we're alright
datetime_format = "%d.%m.%Y %H:%M"
datetime_format_regex = re.compile(r'^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$')

def get_element(_module: str, _name: str) -> type[Any]:
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
    
    raise ValueError(f"could not find element type: {_module}.{_name}")


def object_hook(dct: dict[str, Any]) -> Any:
    """
    Return the de-serialized object
    """
    for key, value in dct.items():
        if isinstance(value, str) and datetime_format_regex.match(value):
            dct[key] = datetime.datetime.strptime(value, datetime_format)
            
    if '_type' in dct and '_module' in dct:
        try:
            obj = get_element(dct["_module"], dct["_type"])
        except ModuleNotFoundError as e:
            raise TypeError("{} in element: {} ({})".format(e, dct["_type"], dct["_module"]))
        
        if obj is None:
            raise ValueError(f'could not get {dct["_module"]}.{dct["_type"]}')
        # class serialized
        if "data" not in dct:
            return obj

        try:
            # use the __from_json__ function if present. __init__ otherwise
            deserializer = getattr(obj, '__from_json__', None)
            if deserializer is None:
                deserializer = obj

            return deserializer(**dct['data'])
            # TODO: find pydantic v2 pendant
            #try:
            #except pydantic.error_wrappers.ValidationError as e:
            #    raise ValueError(f"invalid data: {dct['data']}") from e

        except TypeError as e:

            _, value, traceback = sys.exc_info()
            raise TypeError(f"error in elem: {obj} {e}").with_traceback(traceback)

    else:
        return dct


def add_metadata(data: Any) -> dict[str, Any]:
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


def dumps(obj: Any, add_meta: bool=True) -> str:
    if add_meta:
        obj = add_metadata(obj)
    return json.dumps(obj, cls=Encoder)


def dump(obj: Any, fp: TextIOWrapper, add_meta: bool=True, pretty: bool=True) -> None:
    indent = None
    if pretty:
        indent = 4
    if add_meta:
        obj = add_metadata(obj)
    return json.dump(obj, fp, cls=Encoder, indent=indent)


def loads(obj: str) -> Any:
    raw_data = json.loads(obj)

    miigration = Migration(raw_data)
    if miigration.required:
        return json.loads(miigration.migrate(), object_hook=object_hook)

    return json.loads(obj, object_hook=object_hook)


def load(fp: TextIOWrapper) -> Any:
    raw_data = json.load(fp)
    miigration = Migration(raw_data)
    if miigration.required:
        return json.loads(miigration.migrate(), object_hook=object_hook)
    
    fp.seek(0)

    return json.load(fp, object_hook=object_hook)
