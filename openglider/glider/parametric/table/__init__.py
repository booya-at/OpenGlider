from openglider.glider.parametric.table.material import ClothTable
from openglider.glider.parametric.table.cell.ballooning import BallooningTable
from openglider.glider.parametric.table.cell.cuts import CutTable
from openglider.glider.parametric.table.cell.diagonals import DiagonalTable, StrapTable
from openglider.glider.parametric.table.cell.miniribs import MiniRibTable
from openglider.glider.parametric.table.curve import CurveTable
from openglider.glider.parametric.table.rib.holes import HolesTable
from openglider.glider.parametric.table.rib.singleskin import SingleSkinTable
from openglider.glider.parametric.table.rigidfoil import RibRigidTable, CellRigidTable
from openglider.glider.parametric.table.attachment_points import CellAttachmentPointTable, AttachmentPointTable
from openglider.glider.parametric.table.rib.profile import ProfileTable
from openglider.utils.table import Table
import logging
import io

logger = logging.getLogger(__name__)

class GliderTables:
    cuts: CutTable
    ballooning_factors: BallooningTable
    holes: HolesTable
    diagonals: DiagonalTable
    rigidfoils_rib: RibRigidTable
    rigidfoils_cell: CellRigidTable
    straps: StrapTable
    material_cells: ClothTable
    material_ribs: ClothTable
    miniribs: MiniRibTable
    singleskin_ribs: SingleSkinTable
    profiles: ProfileTable
    attachment_points_rib: AttachmentPointTable
    attachment_points_cell: CellAttachmentPointTable

    def __init__(self, **kwargs):
        for name, _cls in self.__annotations__.items():
            if name in kwargs:
                table = kwargs[name]
            else:
                table = _cls()
            
            setattr(self, name, table)
    
    def __json__(self):
        dct = {}
        for name in self.__annotations__:
            dct[name] = getattr(self, name)
        
        return dct
    
    @classmethod
    def describe(cls):
        text = "# glider tables\n\n"
        for name, _cls in cls.__annotations__.items():
            text += f"## {name}\n\n"

            for keyword_name, keyword in _cls.keywords.items():
                text += f"- {keyword_name}\n"
                text += f"{keyword.describe()}\n"
            
            text += "\n\n"

        return text
    
    def get_rib_sheet(self) -> Table:
        table = Table()
        table.name = "Rib Elements"

        table.append_right(self.profiles.table)
        table.append_right(self.holes.table)
        table.append_right(self.attachment_points_rib.table)
        table.append_right(self.rigidfoils_rib.table)
        table.append_right(self.singleskin_ribs.table)
        table.append_right(self.material_ribs.table)

        for i in range(1, table.num_rows+1):
            table[i, 0] = str(i)

        return table
    
    def get_cell_sheet(self) -> Table:
        table = Table()
        table.name = "Cell Elements"

        table.append_right(self.cuts.table)
        table.append_right(self.diagonals.table)
        table.append_right(self.rigidfoils_cell.table)
        table.append_right(self.straps.table)
        table.append_right(self.material_cells.table)
        table.append_right(self.miniribs.table)
        table.append_right(self.attachment_points_cell.table)

        for i in range(1, table.num_rows+1):
            table[i, 0] = str(i)

        return table


if __name__ == "__main__":
    with open("./Readme.md", "w") as outfile:
        outfile.write(GliderTables.describe())
