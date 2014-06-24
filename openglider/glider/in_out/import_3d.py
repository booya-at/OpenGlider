import custom_json


def import_json(filename):
    #file = open(filename, "r")
    return custom_json.load(filename)
