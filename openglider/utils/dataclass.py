from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, Type, TypeVar

import pydantic
#from pydantic import Field as field
from pydantic import Field  # export Field

from typing_extensions import dataclass_transform
from dataclasses import dataclass as dc, replace

from openglider.utils.cache import CachedProperty, hash_list

if TYPE_CHECKING:
    from pydantic.dataclasses import Dataclass

    OGDataclassT = TypeVar("OGDataclassT", bound="OGDataclass")
    class OGDataclass(Dataclass):
        def __json__(self: OGDataclassT) -> Dict[str, Any]:
            pass

        def copy(self: OGDataclassT) -> OGDataclassT:
            pass

        def __hash__(self: OGDataclassT) -> int:
            pass


class Config:
    arbitrary_types_allowed = True
    #post_init_call = 'after_validation'

@dataclass_transform(kw_only_default=False)
def dataclass(_cls: Type[Any]) -> Type[OGDataclassT]:

    if TYPE_CHECKING:
        _cls_new = dc(_cls)
    else:
        _cls_new = pydantic.dataclasses.dataclass(config=Config)(_cls)
        
    old_json = getattr(_cls, "__json__", None)
    if old_json is None or getattr(old_json, "is_auto", False):
        def __json__(instance: Any) -> Dict[str, Any]:
            return {
                key: getattr(instance, key) for key in _cls_new.__dataclass_fields__
            }
        
        setattr(__json__, "is_auto", True)

        _cls.__json__ = __json__

    old_copy = getattr(_cls, "copy", None)
    if old_copy is None or getattr(old_copy, "is_auto", False):
        def copy(instance: Any) -> Any:
            return  replace(instance)
        
        setattr(copy, "is_auto", True)

        _cls.copy = copy
    
    old_hash = getattr(_cls, "__hash__", None)
    if old_hash is None or getattr(old_hash, "is_auto", False):
        # don't shadow hash (internal python name)
        def _hash(instance: Any) -> int:
            try:
                lst = [getattr(instance, key) for key in _cls_new.__dataclass_fields__]
                return hash_list(lst)
            except Exception as e:
                raise ValueError(f"invalid elem: {instance}") from e

        
        setattr(_hash, "is_auto", True)

        _cls.__hash__ = _hash

        
    return _cls_new

class BaseModel(pydantic.BaseModel):
    _cache: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (CachedProperty,)
        extra = "allow"
        
    def __eq__(self, other: Any) -> bool:
        return other.__class__ == self.__class__ and self.__dict__ == other.__dict__

    def __json__(self) -> Dict[str, Any]:
        return self.dict()
    
    def __hash__(self) -> int:
        return hash_list(self.dict().values())