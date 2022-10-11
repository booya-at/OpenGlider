from __future__ import annotations

import re
from typing import Any, Dict, Tuple
from openglider.utils.colors import Color

class Material:
    weight: float = 0 # g / sqm
    
    manufacturer: str = "generic"
    name: str = "unnamed"
    color: str = ""
    color_code: str = "FFFFFF"

    _regex_color = re.compile(r".*#([A-F0-9a-f]{6})")

    def __init__(self, **kwargs: Any):
        if "color_code" in kwargs:
            color_code = kwargs.pop("color_code")
            self._set_color_code(color_code)
        
        else:
            match = self._regex_color.match(kwargs.get("name", ""))

            if match:
                self._set_color_code(match.group(1))
                
        
        for arg, value in kwargs.items():
            if not hasattr(self, arg):
                raise ValueError(f"invalid attribute: {arg}")
        
            setattr(self, arg, value)
        
    def get_color_rgb(self) -> Tuple[int, int, int]:
        color = Color.parse_hex(self.color_code)
        return (color.r, color.g, color.b)

    def _set_color_code(self, color_code: str) -> None:
        color_code_int = int(color_code, base=16)

        if color_code_int < 0 or color_code_int > int("FFFFFF", base=16):
            raise ValueError(f"invalid color code: {color_code}")
    
        self.color_code = color_code

    def __str__(self) -> str:
        full_name = f"{self.manufacturer}.{self.name}"
        
        if self.color:
            full_name += f".{self.color}"
        
        return full_name
    
    def __repr__(self) -> str:
        return f"<Material: {self.__str__()}>"

    def __json__(self) -> Dict[str, Any]:
        return {
            "name": str(self)
        }
    
    @classmethod
    def __from_json__(cls, name: str) -> Material:
        import openglider.materials
        return openglider.materials.cloth.get(name)
