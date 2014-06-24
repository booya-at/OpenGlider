import json
import openglider.glider.glider


def encode(obj):
    try:
        return json.dumps(obj)
    except TypeError:
        return json.dumps(obj.__dict__)
    #if hasattr(obj, "__toJSON__"):
    #    return obj.__toJSON__
    #else:
    #    return json.dumps(obj)


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return super(Encoder, self).default(obj)
        elif hasattr(obj, "__json__"):
            tha_dict = obj.__json__()
            tha_dict["_type"] = obj.__class__.__module__ + "." + obj.__class__.__name__
            return tha_dict
        else:
            return super(Encoder, self).default(obj)


def dumps(obj):
    return json.dumps({"data": obj,
                       "version": openglider.__version__}, cls=Encoder)


def dump(obj, fp):
    return json.dump({"data": obj,
                      "version": openglider.__version__}, fp, cls=Encoder)

if __name__ == "__main__":
    from openglider import airfoil
    a = airfoil.Profile2D.compute_naca(1234)
    glide = openglider.glider.glider.Glider.import_geometry("/home/simon/Dokumente/OpenGlider/tests/demokite.ods")
    print(json.dumps(a, cls=Encoder))
    print(json.dumps(glide, cls=Encoder))