from __future__ import annotations

import ast
import logging
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Union

import euklid

from openglider.glider.cell.attachment_point import CellAttachmentPoint
from openglider.glider.cell.cell import Cell
from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.base import CellTable, Keyword, RibTable, dto
from openglider.glider.parametric.table.base.parser import Parser
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.glider.rib.rib import Rib
from openglider.glider.rib.singleskin import SingleSkinAttachmentPoint
from openglider.utils.table import Table
from openglider.vector.unit import Angle, Length, Percentage

if TYPE_CHECKING:
    from openglider.glider.glider import Glider
    from openglider.glider.parametric.glider import ParametricGlider

logger = logging.getLogger(__name__)

class ATP(dto.DTO):
    name: str
    rib_pos: Percentage
    force: float | euklid.vector.Vector3D

    #@validator("force", pre=True)
    #def validate_force(self, force: Any):
    #    pass

    def get(self, force: euklid.vector.Vector3D) -> AttachmentPoint:
        data = self.__json__()
        data.pop("force")
        return AttachmentPoint(
            **data,
            force=force
        )


class ATPPROTO(ATP):
    protoloop_distance: Percentage | Length
    
    def get(self, force: euklid.vector.Vector3D) -> AttachmentPoint:
        p = super().get(force)
        p.protoloops = 1
        return p

class ATPPROTO5(ATP):
    protoloop_distance: Percentage | Length
    protoloops: int

class ATPSingleSkin(ATP):
    angle_front: Angle
    angle_back: Angle
    width: Length
    height: Length

    def get(self, force: euklid.vector.Vector3D) -> SingleSkinAttachmentPoint | AttachmentPoint:
        if self.width > 0:
            data = self.__json__()
            data.pop("force")
            return SingleSkinAttachmentPoint(
                **data,
                force=force
            )
        else:
            return AttachmentPoint(
                name=self.name,
                rib_pos=self.rib_pos,
                force=force
            )

# TODO: add DTO*s and ATPPROTO5 (with protoloop count)

class AttachmentPointTable(RibTable):
    regex_node_layer = re.compile(r"([a-zA-Z]*)([0-9]*)")

    keywords = {
        "AHP": Keyword([("name", str), ("pos", float), ("force", Union[float, str])], target_cls=AttachmentPoint),
    }
    dtos = {
        "ATP": ATP,
        "ATPPROTO": ATPPROTO,
        "ATPPROTO5": ATPPROTO5,
        "ATPSingleSkin": ATPSingleSkin
        #"AHP": ATP,
    }

    def get_element(self, row: int, keyword: str, data: list[Any], resolvers: list[Parser]=None, rib: Rib=None, **kwargs: Any) -> AttachmentPoint:
        # rib_no, rib_pos, cell_pos, force, name, is_cell
        force = data[2]

        if isinstance(force, str):
            force = euklid.vector.Vector3D(ast.literal_eval(force))
        elif rib is not None:
            force = AttachmentPoint.calculate_force_rib_aligned(rib, force)

        if keyword in self.dtos:
            if resolvers is None:
                raise ValueError()
            dto: type[ATP] = self.dtos[keyword]  # type: ignore
            data[2] = 0.
            dct = self._prepare_dto_data(row, dto, data, resolvers)

            return dto(**dct).get(force=force)
        
        return super().get_element(row, keyword, data)
    
    def apply_forces(self, forces: Mapping[str, euklid.vector.Vector3D | float]) -> None:
        new_table = Table()

        def update_columns(keyword: str, data_length: int, force_position: int) -> None:
            for column in self.get_columns(self.table, keyword, data_length):
                for row in range(2, column.num_rows):
                    name = column[row, 0]
                    if name:
                        if name in forces:
                            force = forces[name]
                            try:
                                if isinstance(force, float):
                                    raise TypeError()
                                column[row, force_position] = str(list(force))
                            except TypeError:
                                column[row, force_position] = force
                        else:
                            logger.warning(f"no force for {name}")
                
                new_table.append_right(column)


        for keyword_name, keyword in self.keywords.items():
            data_length = keyword.attribute_length
            update_columns(keyword_name, data_length, 2)
        
        for keyword_name, dto in self.dtos.items():
            data_length = len(dto.describe())
            update_columns(keyword_name, data_length, 2)
            
        
        self.table = new_table
    
    @classmethod
    def from_glider(cls, glider: Glider) -> ParametricGlider:
        raise NotImplementedError()


class CellAttachmentPointTable(CellTable):
    keywords = {
        "ATP": Keyword([("name", str), ("cell_pos", float), ("rib_pos", float), ("force", Union[float, str])], target_cls=CellAttachmentPoint),
        "AHP": Keyword([("name", str), ("cell_pos", float), ("rib_pos", float), ("force", Union[float, str])], target_cls=CellAttachmentPoint),
        "ATPDIFF": Keyword([("name", str), ("cell_pos", float), ("rib_pos", float), ("force", Union[float, str]), ("offset", float)], target_cls=CellAttachmentPoint)
    }

    def get_element(self, row: int, keyword: str, data: list[Any], curves: dict[str, GliderCurveType]={}, cell: Cell=None, **kwargs: Any) -> CellAttachmentPoint:
        force = data[3]

        if isinstance(force, str):
            force = euklid.vector.Vector3D(ast.literal_eval(force))
        elif cell is not None:
            force = CellAttachmentPoint.calculate_force_cell_aligned(cell, force)


        node = CellAttachmentPoint(name=data[0], cell_pos=data[1], rib_pos=data[2], force=force)

        if len(data) > 4:
            offset = data[4]
            if isinstance(offset, str):
                offset = curves[offset].get(row)
            
            node.offset = offset

        return node

    def from_glider(self, glider: Glider) -> CellAttachmentPointTable:
        raise NotImplementedError()
