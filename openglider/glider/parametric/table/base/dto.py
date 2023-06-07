


import abc
import types
from typing import Any, Callable, Generator, Generic, Self, TypeVar

from pydantic.generics import GenericModel

from openglider.utils.dataclass import BaseModel

ReturnType = TypeVar("ReturnType")
TupleType = TypeVar("TupleType")

class CellTuple(GenericModel, Generic[TupleType]):
    first: TupleType
    second: TupleType

    # pydantic support
    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Self], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> Self:
        if isinstance(v, tuple) and len(v) == 2:
            return cls(
                first=v[0],
                second=v[1]
            )
        else:
            return cls(
                first=v,
                second=v
            )


class DTO(Generic[ReturnType], BaseModel, abc.ABC):
    _types: list[tuple[str, str]] | None = None

    def get_object(self) -> ReturnType:

        raise NotImplementedError
    
    @staticmethod
    def _get_type_string(type_: type) -> str:
        if isinstance(type_, types.UnionType):
            names = []
            for subtype in type_.__args__:
                names.append(subtype.__name__)
            
            return " | ".join(names)
        else:
            return type_.__name__
    
    @staticmethod
    def _is_cell_tuple(type: Any) -> CellTuple | None:
        try:
            if issubclass(type, CellTuple):
                return type
        except TypeError:
            pass

        return None

    @classmethod
    def describe(cls) -> list[tuple[str, str]]:
        if cls._types is None:
            result = []
            for field in cls.__fields__.values():
                is_cell_tuple = cls._is_cell_tuple(field.type_)

                if is_cell_tuple:
                    inner_type = is_cell_tuple.__fields__["first"].type_
                    inner_type_str = cls._get_type_string(inner_type)

                    for side in ("1", "2"):
                        result.append((f"{field.name} ({side})", inner_type_str))
                
                else:
                    result.append((field.name, cls._get_type_string(field.type_)))
            
            cls._types = result
        
        return cls._types
        
    @classmethod
    def column_length(cls) -> int:
        return len(cls.describe())
