from typing import Any, Generic, Iterator, List, Tuple, TypeVar

from openglider.utils.cache import recursive_getattr
#from openglider.utils.table import Table


def sign(val: float) -> int:
    val = float(val)
    return (val > 0) - (val < 0)


def consistent_value(elements: List[Any], attribute: str) -> Any:
    vals = [recursive_getattr(element, attribute) for element in elements]
    if vals[1:] == vals[:-1]:
        return vals[0]
    
    raise Exception("values not consistent: {attribute}, {elements}")


def linspace(start: float, stop: float, count: int) -> List[float]:
    return [start + y/(count-1) * (stop-start) for y in range(count)]


T = TypeVar("T")

class ZipCmp(Generic[T]):
    def __init__(self, list: List[T]):
        self.list = list

    def __iter__(self) -> Iterator[Tuple[T, T]]:
        for x, y in zip(self.list[:-1], self.list[1:]):
            yield x, y
