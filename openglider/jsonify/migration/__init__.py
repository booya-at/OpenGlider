import re
import json
import io


def migrate(jsondata):
    jsondata_new = migrate_00(jsondata)
    with io.StringIO() as stream:
        return json.dump(jsondata_new, stream)


def migrate_00(jsondata):
    """
    Alter data and return
    :param jsondata:
    :return:
    """
    for node in find_nodes(jsondata, name=r"DrawingArea"):
        node["__class__"] = "Layout"


def find_nodes(jsondata, name="*", module=r"*"):
    """
    Find nodes recursive
    :param name: *to find any
    :param jsondata:
    :return:
    """
    rex_name = re.compile(name)
    rex_module = re.compile(module)
    nodes = []
    if isinstance(jsondata, dict):
        if "__class__" in jsondata:
            # node
            if rex_name.match(jsondata["__class__"]) and rex_module.match(jsondata["__module__"]):
                nodes.append(jsondata)

        if isinstance(jsondata, dict):
            for el in jsondata.values():
                nodes += find_nodes(el, name, module)
        elif isinstance(jsondata, str):
            pass
        else:
            try:
                for el in jsondata:
                    nodes += find_nodes(el, name, module)
            except TypeError:
                pass

    return nodes



migrations = {
    "0.00":
}