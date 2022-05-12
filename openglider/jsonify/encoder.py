import json
import re
import datetime


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
            return str(obj)
        elif hasattr(obj, "__json__"):
            result = obj.__json__()

            if type(result) == dict:
                type_str = str(obj.__class__)
                module = obj.__class__.__module__
                type_regex = "<class '{}\.(.*)'>".format(module.replace(".", "\."))
                match = re.match(type_regex, type_str)
                if match is None:
                    raise ValueError(f"couldn't match type: {type_str}")
                class_name = match.group(1)

                return {"_type": class_name,
                        "_module": module,
                        "data": obj.__json__()}
            else:
                return result
        else:
            try:
                return super(Encoder, self).default(obj)
            except TypeError as e:
                raise TypeError(f"can not convert {obj}") from e
