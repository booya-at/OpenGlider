from typing import Any, Generic, List, Tuple, TypeVar
from collections.abc import Iterator

from openglider.utils.cache import recursive_getattr
#from openglider.utils.table import Table


def sign(val: float) -> int:
    val = float(val)
    return (val > 0) - (val < 0)


def consistent_value(elements: list[Any], attribute: str) -> Any:
    vals = [recursive_getattr(element, attribute) for element in elements]
    if vals[1:] == vals[:-1]:
        return vals[0]
    
    raise Exception("values not consistent: {attribute}, {elements}")


def linspace(start: float, stop: float, count: int) -> list[float]:
    return [start + y/(count-1) * (stop-start) for y in range(count)]


T = TypeVar("T")

class ZipCmp(Generic[T]):
    def __init__(self, list: list[T]):
        self.list = list

    def __iter__(self) -> Iterator[tuple[T, T]]:
        yield from zip(self.list[:-1], self.list[1:])
