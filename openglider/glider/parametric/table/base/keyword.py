import logging
import typing
from typing import Generic, TypeVar, Union

from openglider.utils.table import Table

logger = logging.getLogger(__name__)


ElementType = TypeVar("ElementType")
KeywordsType = list[Union[tuple[str, typing.Any], str]]

class Keyword(Generic[ElementType]):
    NoneType = typing.Any
    target_cls: typing.Any = dict
    def __init__(self, attributes: KeywordsType | None=None, description: str="", target_cls: type[ElementType]=None):
        if attributes is None:
            if target_cls is not None:
                attributes = list(typing.get_type_hints(target_cls.__init__).keys())
            else:
                raise ValueError(f"invalid configuration for Keyword: {self}")

        self.attributes: list[tuple[str, typing.Any]] = []
        annotations = {}
        if target_cls:
            annotations = typing.get_type_hints(target_cls.__init__)

        for attribute in attributes:
            if isinstance(attribute, str):
                attribute_name = attribute
                attribute_type = annotations.get(attribute, self.NoneType)
            else:
                attribute_name, attribute_type = attribute

            if attribute_type is self.NoneType:
                logger.debug(f"invalid type for {attribute}: {attribute_type} {type(attribute_type)} ({target_cls})")
            
            self.attributes.append((attribute_name, attribute_type))

        self.description = description
        self.target_cls = target_cls
    
    @property
    def attribute_length(self) -> int:
        return len(self.attributes)
    
    def get_attribute_names(self) -> typing.Iterable[str]:
        for name, dtype in self.attributes:
            yield f"{name}: {dtype.__name__}"
    
    def describe(self) -> str:
        description = f"  * length: {self.attribute_length}"
        if self.attributes:
            description += f"\n  * attributes: "
            description += ", ".join(self.get_attribute_names())
        if self.description:
            description += f"\n  * description: {self.description}"
        
        return description
    
    def get_header(self, name: str) -> Table:
        # TODO: move the name into the keyword
        table = Table()
        table[0, 0] = name
        for i, attribute in enumerate(self.get_attribute_names()):
            table[1, i] = attribute

        return table

    def get(self, keyword: str, data: list[typing.Any]) -> ElementType:
        init_kwargs = {}

        for (name, target_type), value in zip(self.attributes, data):
            if target_type != self.NoneType and not isinstance(value, target_type):
                logger.warning(f"wrong type: {keyword}/{name}: {value} converting to {target_type}")
                value = target_type(value)
            
            init_kwargs[name] = value

        return self.target_cls(**init_kwargs)
