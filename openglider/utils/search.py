

from typing import Iterable, Tuple, TypeVar, Callable

ObjectType = TypeVar("ObjectType")
MatchFunction = Callable[[ObjectType], bool]

def search(objects: Iterable[ObjectType], match_function: MatchFunction) -> Tuple[int, ObjectType]:
    for i, obj in enumerate(objects):
        if match_function(obj):
            return i, obj
    
    raise ValueError("Item not found")