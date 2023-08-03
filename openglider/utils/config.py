from __future__ import annotations

import inspect
import json
import html
from pathlib import Path
from typing import Any
from collections.abc import Iterator

from pydantic import parse_obj_as
import logging

from openglider.utils.dataclass import BaseModel

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, dct: dict[str, Any] | Config | None=None):
        self.__dict__ = {}

        items = inspect.getmembers(self.__class__, lambda a:not(inspect.isroutine(a)))
        annotations = self.get_annotations()
        for key, value in items:
            if key in annotations:
                try:
                    value = annotations[key](value)
                except Exception:
                    pass
            if not key.startswith('_') and key != "get":
                self.__dict__[key] = value

        self.update(dct)

    
    @classmethod
    def get_annotations(cls) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for c in cls.mro():
            try:
                d.update(**c.__annotations__)
            except AttributeError:
                # object, at least, has no __annotations__ attribute.
                pass
        return d

    def __json__(self) -> dict[str, Any]:
        return {
            "dct": self.__dict__
        }

    def __repr__(self) -> str:
        repr_str = f"{self.__class__}\n"
        width = max([len(x) for x in self.__dict__])
        for key, value in self.__dict__.items():
            repr_str += "    -{0: <{width}} -> {value}\n".format(key, value=value, width=width)

        return repr_str

    def _repr_html_(self) -> str:
        html_str = """<table>\n"""
        for key, value in self.__dict__.items():
            html_str += f"""    <tr>
                <td>{key}</td>
                <td>{html.escape(repr(value))}</td>
                </tr>
            """
        
        html_str += "</table>"

        return html_str


    def __iter__(self) -> Iterator[tuple[str, Any]]:
        for key, value in self.__dict__.items():
            if key != "get":
                yield key, value
        for key, value in self.__class__.__dict__.items():
            if not key.startswith("_"):
                yield key, value

    def __getitem__(self, item: str) -> Any:
        return self.__getattribute__(item)

    def get(self, key: str, default: Any=None) -> Any:
        if hasattr(self, key):
            return self.__getattribute__(key)
        else:
            return default

    def update(self, dct: dict[str, Any] | Config | None) -> None:
        if dct is None:
            return

        self.__dict__.update(dct)

    def write(self, filename: str) -> None:
        import openglider.jsonify
        with open(filename, "w") as jsonfile:
            openglider.jsonify.dump(self, jsonfile)

    @classmethod
    def read(cls, filename: str) -> Config:
        with open(filename) as jsonfile:
            data = json.load(jsonfile)

        return cls(data["data"]["data"]["dct"])


class ConfigNew(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    def __json__(self) -> dict[str, Any]:
        return {
            "dct": self.__dict__
        }

    def _repr_html_(self) -> str:
        html_str = """<table>\n"""
        for key, value in self.__dict__.items():
            html_str += f"""    <tr>
                <td>{key}</td>
                <td>{html.escape(repr(value))}</td>
                </tr>
            """
        
        html_str += "</table>"

        return html_str

    def write(self, filename: str) -> None:
        import openglider.jsonify
        with open(filename, "w") as jsonfile:
            openglider.jsonify.dump(self, jsonfile)

    @classmethod
    def read(cls, filename: str | Path) -> ConfigNew:
        with open(filename) as jsonfile:
            data = json.load(jsonfile)

        return parse_obj_as(cls, data["data"]["data"]["dct"])
