from typing import Any, Dict, List
from openglider.glider import curve
from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.base import RibTable, Keyword
from openglider.glider.parametric.table.base.dto import DTO
from openglider.glider.parametric.table.base.parser import Parser

from openglider.glider.rib.crossports import RibHole, RibSquareHole, MultiSquareHole, AttachmentPointHole

import logging

from openglider.vector.unit import Angle, Length, Percentage

logger = logging.getLogger(__name__)

class HoleDTO(DTO):
    pos: Percentage
    size: Percentage

    def get_object(self) -> RibHole:
        return RibHole(
            pos=self.pos,
            size=self.size
        )

class HoleSQDTO(DTO):
    x: Percentage
    width: Percentage
    height: Percentage

    def get_object(self) -> RibSquareHole:
        return RibSquareHole(
            x=self.x,
            width=self.width,
            height=self.height
        )

class Hole5DTO(HoleDTO):
    width: Percentage
    vertical_shift: Percentage
    rotation: Angle

    def get_object(self) -> RibHole:
        hole = super().get_object()
        hole.vertical_shift = self.vertical_shift
        hole.rotation = self.rotation

        return hole
    
class HoleSqMultiDTO(DTO):
    start: Percentage
    end: Percentage
    height: Percentage
    num_holes: int
    border_width: Percentage | Length

    def get_object(self) -> MultiSquareHole:
        return MultiSquareHole(
            start=self.start, end=self.end, height=self.height,
            num_holes=self.num_holes, border_width=self.border_width
        )

class HoleSqMulti6(HoleSqMultiDTO):
    margin: Percentage | Length

    def get_object(self) -> MultiSquareHole:
        hole = super().get_object()
        hole.margin = self.margin

        return hole

class HoleATP(DTO):
    start: Percentage
    end: Percentage
    num_holes: int

    def get_object(self) -> AttachmentPointHole:
        return AttachmentPointHole(
            **self.dict()
        )

class HOLEATP5(HoleATP):
    border: Length | Percentage
    side_boder: Length | Percentage

class HOLEATP6(HOLEATP5):
    corner_size: Percentage


class HolesTable(RibTable):
    dtos = {
        "HOLE": HoleDTO,
        "QUERLOCH": HoleDTO,
        "HOLESQ": HoleSQDTO,
        "HOLE5": Hole5DTO,
        "HOLESQMULTI": HoleSqMultiDTO,
        "HOLESQMULTI6": HoleSqMulti6,
        "HOLEATP": HoleATP,
        "HOLEATP5": HOLEATP5,
        "HOLEATP6": HOLEATP6,
    }
