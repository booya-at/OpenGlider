import json
import time
from openglider.jsonify.objects import objects
import openglider

__ALL__ = ['dumps', 'dump', 'loads', 'load']

# Main json-export routine.
# Maybe at some point it can become necessary to de-reference classes with _module also,
# because of same-name-elements....
# For the time given, we're alright


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if obj.__class__.__module__ == 'numpy':
            return obj.tolist()
        elif hasattr(obj, "__json__"):
            return {"_type": obj.__class__.__name__,
                    "_module": obj.__class__.__module__,
                    "data": obj.__json__()}
        else:
            return super(Encoder, self).default(obj)


def object_hook(dct):
    """
    Return the de-serialized object
    """
    if '_type' in dct and '_module' in dct:
        _module = dct['_module'].split('.')
        _type = dct['_type']
        if _type in objects:
            obj = objects[_type]
            # TODO: add allowed_modules['_module']
        else:
            raise LookupError("No element of type {} found (module: {})".format(_type, dct['_module']))

        try:
            # use the __from_json__ function if present. __init__ otherwise
            deserializer = getattr(obj, '__from_json__', obj)
            return deserializer(**dct['data'])
        except TypeError as e:
            raise TypeError("{} in element: {} ({})".format(e, _type, deserializer))

    else:
        return dct


def add_metadata(data):
    if isinstance(data, dict) and 'MetaData' in data:
        data['MetaData']['date_modified'] = time.strftime("%d.%m.%y %H:%M")
        return data
    else:
        return {'MetaData': {'application': 'openglider',
                             'version': openglider.__version__,
                             'author': 'obviously, a pilot',
                             'date_created': time.strftime("%d.%m.%y %H:%M"),
                             'date_modified': time.strftime("%d.%m.%y %H:%M")},
                'data': data}


def dumps(obj):
    return json.dumps(add_metadata(obj), cls=Encoder)


def dump(obj, fp):
    return json.dump(add_metadata(obj), fp, cls=Encoder, indent=4)


def loads(obj):
    return json.loads(obj, object_hook=object_hook)


def load(fp):
    return json.load(fp, object_hook=object_hook)