import json
import time
import openglider.glider.ballooning
import openglider.glider.glider
from openglider.graphics import draw_glider
import openglider.utils

__ALL__ = ['dumps', 'dump', 'loads', 'load', 'update_legacy_file']

def return_glider(ribs, cells, lines=None):
    for cell in cells:
        if isinstance(cell.rib1, int):
            cell.rib1 = ribs[cell.rib1]
        if isinstance(cell.rib2, int):
            cell.rib2 = ribs[cell.rib2]
    return openglider.Glider(cells)

objects = {"Glider": return_glider,
           "Rib": openglider.glider.Rib,
           "Cell": openglider.glider.Cell,
           "BallooningBezier": openglider.glider.ballooning.BallooningBezier,
           "Profile2D": openglider.airfoil.Profile2D}


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return super(Encoder, self).default(obj)
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
            #try:
            return objects[_type](**dct['data'])
            #except:
            #    raise ValueError()
        else:
            raise LookupError("No element of type {} found (module: {})".format(_type, dct['_module']))
    else:
        return dct


def update_legacy_file(dct):
    if 'version' in dct:
        pass


def add_meta_info(data):
    return {'MetaData': {'application': 'openglider',
                         'version': openglider.__version__,
                         'author': 'obviously, a pilot',
                         'date_created': time.strftime("%d.%m.%y %H:%M")},
            'data': data}


def dumps(obj):
    return json.dumps(add_meta_info(obj), cls=Encoder)


def dump(obj, fp):
    return json.dump(add_meta_info(obj), fp, cls=Encoder, indent=2)


def loads(obj):
    return json.loads(obj, object_hook=object_hook)


def load(fp):
    return json.load(fp, object_hook=object_hook)


if __name__ == "__main__":
    from openglider import airfoil
    a = airfoil.Profile2D.compute_naca(1234)
    glide = openglider.glider.glider.Glider.import_geometry("/home/simon/Dokumente/OpenGlider/tests/demokite.ods")
    print(dumps(a))
    jj = dumps(glide)
    glide2 = loads(jj)
    with open("/tmp/glider.json", 'w') as exportfile:
        dump(glide, exportfile)

    #print(loads("{'_type': Profile2D, 'data': [[1,2],[2,3]]"))
    print(glide2)
    #draw_glider(glide2['data'])