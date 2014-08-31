import json
import time
import numpy
from .objects import objects
import openglider

__ALL__ = ['dumps', 'dump', 'loads', 'load']

# Main json-export routine.
# Maybe at some point it can become necessary to de-reference classes with _module also,
# because of same-name-elements....


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return super(Encoder, self).default(obj)
        elif isinstance(obj, numpy.ndarray):
            return super(Encoder, self).default(obj.tolist())
        elif hasattr(obj, "__json__"):
            return {"_type": obj.__class__.__name__,
                    "_module": obj.__class__.__module__,
                    "data": obj.__json__()}
        else:
            return super(Encoder, self).default(obj)


def object_hook(dct):
    #print("jo")
    if '_type' in dct and '_module' in dct:
        _type = dct['_type']
        if _type in objects:
            try:
                return objects[_type](**dct['data'])
            except TypeError as e:
                raise TypeError(e.message + " in element: {}".format(_type))
        else:
            raise LookupError("No element of type {} found (module: {})".format(_type, dct['_module']))
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


if __name__ == "__main__":
    from openglider import airfoil
    a = airfoil.Profile2D.compute_naca(1234)
    glide = openglider.glider.Glider.import_geometry("../../tests/demokite.ods")
    #print(dumps(a))
    jj = dumps(glide)
    glide2 = loads(jj)
    with open("/tmp/glider.json", 'w') as exportfile:
        dump(glide, exportfile)

    #print(loads("{'_type': Profile2D, 'data': [[1,2],[2,3]]"))
    print(glide2)
    #draw_glider(glide2['data'])