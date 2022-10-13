from __future__ import annotations

from typing import Iterator, List, Tuple
from openglider.utils.dataclass import dataclass
import euklid

@dataclass
class Color:
    r: int
    g: int
    b: int
    name: str="unnamed color"

    def __iter__(self) -> Iterator[int]:
        for x in (self.r, self.g, self.b):
            yield x

    def hex(self) -> str:
        return f"{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def parse_hex(cls, hex: str) -> Color:
        if hex.startswith("#"):
            hex = hex[1:]
        
        factor = 1
        if len(hex) == 3:
            rgb = list(hex)
            factor = 17
        elif len(hex) == 6:
            rgb = [
                hex[:2],
                hex[2:4],
                hex[4:]
            ]
        else:
            raise ValueError(f"{hex} is not a valid color")
        
        r,g,b = [int(x, base=16)*factor for x in rgb]

        return cls(r, g, b, name=f"#{hex}")
    

def colorwheel(num: int) -> List[Tuple[int, int, int]]:
    # r = 0
    # g = 1/3
    # b = 2/3
    colors = []
    for i in range(num):
        alpha = (i/num)
        red = max(0, 1 - 3*abs(alpha))
        green = max(0, 1 - 3*abs(1/3 - alpha))  # 1/3 -> 1, 0->0, 2/3->0
        blue = max(0, 1 - 3*abs(2/3 - alpha))

        rgb = [int(255*x) for x in (red, green, blue)]
        factor = 255 / max(rgb)
        rgb_normalized = [min(255, int(factor*x)) for x in rgb]
        colors.append(tuple(rgb_normalized))

    return colors

class HeatMap():
    _interpolation_red = euklid.vector.Interpolation([
        [0, 0],
        [0.35, 0],
        [0.66, 1],
        [1, 1]
    ])

    _interpolation_blue = euklid.vector.Interpolation([
        [0, 1],
        [0.34, 1],
        [0.65, 0],
        [1, 0]
    ])

    _interpolation_green = euklid.vector.Interpolation([
        [0, 0],
        [0.125, 0],
        [0.375, 1],
        [0.64, 1],
        [0.91, 0],
        [1, 0]
    ])

    def __init__(self, min_value: float=0, max_value: float=100):
        self.min_value = min_value
        self.max_value = max_value

    @classmethod
    def from_data(cls, data: List[float]) -> HeatMap:
        min_value = min(data)
        max_value = max(data)
        if abs(max_value - min_value) < 1e-5:
            max_value += 0.1
        return cls(min_value, max_value)
    
    def __call__(self, value: float) -> Tuple[int, int, int]:
        pct_raw = (value - self.min_value) / (self.max_value - self.min_value)
        pct = min(1., max(0, pct_raw))

        red = self._interpolation_red.get_value(pct)
        blue = self._interpolation_blue.get_value(pct)
        green = self._interpolation_green.get_value(pct)

        return (
            int(red * 255),
            int(green * 255),
            int(blue * 255)
        )
