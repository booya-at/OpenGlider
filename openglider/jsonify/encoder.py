import inspect
import json
import re
import datetime
from typing import Any


# Main json-export routine.
# Maybe at some point it can become necessary to de-reference classes with _module also,
# because of same-name-elements....
# For the time given, we're alright
datetime_format = "%d.%m.%Y %H:%M"
datetime_format_regex = re.compile(r'^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$')

class Encoder(json.JSONEncoder):
    def default(self, obj: Any) -> dict[str, Any] | str | list[Any]:
        if obj.__class__.__module__ == 'numpy':
            return obj.tolist()
        elif isinstance(obj, datetime.datetime):
            return str(obj)
        elif hasattr(obj, "__json__"):
            if inspect.isclass(obj):
                return {
                    "_type": obj.__name__,
                    "_module": obj.__module__,
                }

            try:
                result = obj.__json__()
            except Exception as e:
                print(e)
                raise ValueError(f"could not convert object: {obj}")

            if type(result) == dict:
                type_str = str(obj.__class__)
                module = obj.__class__.__module__
                type_regex = r"<class '{}\.(.*)'>".format(module.replace(".", r"\."))
                match = re.match(type_regex, type_str)
                if match is None:
                    raise ValueError(f"couldn't match type: {type_str}")
                class_name = match.group(1)

                return {
                    "_type": class_name,
                    "_module": module,
                    "data": result
                }
            else:
                return result
        else:
            try:
                return super().default(obj)
            except TypeError as e:
                raise TypeError(f"can not convert {obj}") from e
