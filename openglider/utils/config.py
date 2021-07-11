
import inspect
import json
import html

from openglider.utils.cache import recursive_getattr


class Config(object):
    def __init__(self, dct=None):
        self.__dict__ = {}
        items = inspect.getmembers(self.__class__, lambda a:not(inspect.isroutine(a)))
        for key, value in items:
            if not key.startswith('_') and key != "get":
                self.__dict__[key] = value

        self.update(dct)

    def __json__(self):
        return {
            "dct": self.__dict__
        }

    def __repr__(self):
        repr_str = "{}\n".format(self.__class__)
        width = max([len(x) for x in self.__dict__])
        for key, value in self.__dict__.items():
            repr_str += "    -{0: <{width}} -> {value}\n".format(key, value=value, width=width)

        return repr_str

    def _repr_html_(self):
        html_str = """<table>\n"""
        for key, value in self.__dict__.items():
            html_str += f"""    <tr>
                <td>{key}</td>
                <td>{html.escape(repr(value))}</td>
                </tr>
            """
        
        html_str += "</table>"

        return html_str


    def __iter__(self):
        for key, value in self.__dict__.items():
            if key != "get":
                yield key, value
        #return self.__dict__.__iter__()

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def get(self, key, default=None):
        if hasattr(self, key):
            return self.__getattribute__(key)
        else:
            return default

    def update(self, dct):
        if dct is None:
            return

        self.__dict__.update(dct)

    def write(self, filename):
        import openglider.jsonify
        with open(filename, "w") as jsonfile:
            openglider.jsonify.dump(self, jsonfile)

    @classmethod
    def read(cls, filename):
        with open(filename, "r") as jsonfile:
            data = json.load(jsonfile)

        return cls(data["data"]["data"]["dct"])
