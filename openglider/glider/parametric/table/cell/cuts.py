import logging

from openglider.glider.cell.panel import PANELCUT_TYPES, PanelCut
from openglider.glider.parametric.table.base import CellTable
from openglider.glider.parametric.table.base.dto import DTO, CellTuple
from openglider.vector.unit import Length, Percentage

logger = logging.getLogger(__name__)

class DesignCut(DTO):
    x: CellTuple[Percentage]
    cut_type = PANELCUT_TYPES.orthogonal

    def get_object(self) -> PanelCut:
        print("jo", self.cut_type)
        return PanelCut(
            x_left=self.x.first,
            x_right=self.x.second,
            cut_type=self.cut_type
        )

class FoldedCut(DesignCut):
    pass
    #cut_type = PANELCUT_TYPES.folded

class Cut3D(DesignCut):
    cut_type = PANELCUT_TYPES.cut_3d

class SingleSkinCut(DesignCut):
    cut_type = PANELCUT_TYPES.singleskin

class CutRound(DesignCut):
    center: Percentage
    amount: Length
    cut_type = PANELCUT_TYPES.round

    def get_object(self) -> PanelCut:
        cut = super().get_object()
        cut.x_center = self.center
        cut.seam_allowance = self.amount

        return cut

class CutTable(CellTable):
    dtos = {
        "DESIGNM": DesignCut,
        "DESIGNO": DesignCut,
        "orthogonal": DesignCut,

        "EKV": FoldedCut,
        "EKH": FoldedCut,
        "folded": FoldedCut,

        "CUT3D": Cut3D,
        "cut_3d": Cut3D,

        "singleskin": SingleSkinCut,
    }
