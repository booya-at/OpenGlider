from typing import TYPE_CHECKING
from dataclasses import dataclass as dc
from dataclasses import asdict
from dataclasses import field

def dataclass(_cls):
    _cls_new = dc(_cls)

    if not hasattr(_cls_new, "__json__"):
        _cls_new.__json__ = lambda instance: {
            key: getattr(instance, key) for key in _cls_new.__dataclass_fields__   
        }

    return _cls_new
