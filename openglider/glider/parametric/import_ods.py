from __future__ import annotations

import logging
import math
import numbers
from typing import TYPE_CHECKING
from packaging.version import Version

import euklid
import pyfoil

from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.config import ParametricGliderConfig, SewingAllowanceConfig
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.table import GliderTables
from openglider.glider.parametric.table.attachment_points import AttachmentPointTable, CellAttachmentPointTable
from openglider.glider.parametric.table.ballooning import BallooningTable, transpose_columns
from openglider.glider.parametric.table.cell.ballooning import BallooningModifierTable
from openglider.glider.parametric.table.cell.cuts import CutTable
from openglider.glider.parametric.table.cell.diagonals import DiagonalTable, StrapTable
from openglider.glider.parametric.table.cell.miniribs import MiniRibTable
from openglider.glider.parametric.table.curve import CurveTable
from openglider.glider.parametric.table.lines import LineSetTable
from openglider.glider.parametric.table.material import CellClothTable, RibClothTable
from openglider.glider.parametric.table.rib.holes import HolesTable
from openglider.glider.parametric.table.rib.profile import ProfileModifierTable
from openglider.glider.parametric.table.rib.rib import SingleSkinTable
from openglider.glider.parametric.table.rigidfoil import CellRigidTable, RibRigidTable
from openglider.utils import linspace
from openglider.utils.dataclass import BaseModel
from openglider.utils.table import Table
from openglider.utils.types import SymmetricCurveType

if TYPE_CHECKING:
    from openglider.glider.parametric import ParametricGlider

logger = logging.getLogger(__name__)

class TableNames:
    cell_sheet = "Cell Elements"
    rib_sheet = "Rib Elements"
    parametric_data = "Parametric"


def import_ods_2d(cls: type[ParametricGlider], filename: str) -> ParametricGlider:
    logger.info(f"Import file: {filename}")
    tables = Table.load(filename)

    return import_ods_glider(cls, tables)


def import_ods_glider(cls: type[ParametricGlider], tables: list[Table]) -> ParametricGlider:
    table_dct: dict[str, Table] = {
        TableNames.cell_sheet: tables[1],
        TableNames.rib_sheet: tables[2]
    }

    for table in tables[3:]:
        if table.name in table_dct:
            raise ValueError(f"{table.name} already in tables")
        table_dct[table.name] = table

    cell_sheet = tables[1]
    rib_sheet = tables[2]

    config = ParametricGliderConfig.read_table(tables[7])
    sewing_allowances = SewingAllowanceConfig.read_table(table_dct.get(SewingAllowanceConfig.table_name, Table()))


    logger.info(f"Loading file version {config.version}")
    # ------------

    # profiles = [BezierProfile2D(profile) for profile in transpose_columns(sheets[3])]
    profiles = [pyfoil.Airfoil(profile, name).normalized() for name, profile in transpose_columns(tables[3])]

    if config.version > Version("0.0.1"):
        has_center_cell = not tables[0]["C2"] == 0
        cell_no = (tables[0].num_rows - 2) * 2 + has_center_cell
        geometry = get_geometry_parametric(table_dct[TableNames.parametric_data], cell_no, config)
    else:
        geometry = get_geometry_explicit(tables[0], config)
        has_center_cell = geometry.shape.has_center_cell

    balloonings = BallooningTable(table=table_dct[BallooningTable.table_name])

    attachment_points_lower = config.get_lower_attachment_points()
    lineset_table = LineSetTable(table=table_dct[LineSetTable.table_name], lower_attachment_points=attachment_points_lower)

    migrate_header = cell_sheet[0, 0] is not None and cell_sheet[0, 0] < "V4"

    glider_tables = GliderTables()
    glider_tables.curves = CurveTable(table_dct.get("Curves", None), config.version)

    glider_tables.cuts = CutTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.ballooning_modifiers = BallooningModifierTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.holes = HolesTable(rib_sheet, migrate_header=migrate_header)
    glider_tables.diagonals = DiagonalTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.rigidfoils_rib = RibRigidTable(rib_sheet, migrate_header=migrate_header)
    glider_tables.rigidfoils_cell = CellRigidTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.straps = StrapTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.material_cells = CellClothTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.material_ribs = RibClothTable(rib_sheet, migrate_header=migrate_header)
    glider_tables.miniribs = MiniRibTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.rib_modifiers = SingleSkinTable(rib_sheet, migrate_header=migrate_header)
    glider_tables.profile_modifiers = ProfileModifierTable(rib_sheet, migrate_header=migrate_header)
    glider_tables.attachment_points_rib = AttachmentPointTable(rib_sheet, migrate_header=migrate_header)
    glider_tables.attachment_points_cell = CellAttachmentPointTable(cell_sheet, migrate_header=migrate_header)
    glider_tables.lines = lineset_table
    
    glider_2d = cls(tables=glider_tables,
                         profiles=profiles,
                         balloonings=balloonings.get(),
                         allowances=sewing_allowances,
                         config=config,
                         speed=config.speed,
                         glide=config.glide,
                         **geometry.model_dump())

    return glider_2d


class Geometry(BaseModel):
    shape: ParametricShape
    arc: ArcCurve
    aoa: SymmetricCurveType
    profile_merge_curve: SymmetricCurveType
    ballooning_merge_curve: SymmetricCurveType


def get_geometry_explicit(sheet: Table, config: ParametricGliderConfig) -> Geometry:
    # All Lists
    front = []
    back = []
    cell_distribution = []
    aoa = []
    arc = []
    profile_merge = []
    ballooning_merge = []

    y = z = span_last = alpha = 0.
    for i in range(1, sheet.num_rows):
        line = [sheet[i, j] for j in range(sheet.num_columns)]
        if not line[0]:
            break  # skip empty line
        if not all(isinstance(c, numbers.Number) for c in line[:10]):
            raise ValueError(f"Invalid row ({i}): {line}")
        # Index, Choord, Span(x_2d), Front(y_2d=x_3d), d_alpha(next), aoa,
        chord = line[1]
        span = line[2]
        x = line[3]
        y += math.cos(alpha) * (span - span_last)
        z -= math.sin(alpha) * (span - span_last)

        alpha += line[4] * math.pi / 180  # angle after the rib

        aoa.append([span, line[5] * math.pi / 180])
        arc.append([y, z])
        front.append([span, -x])
        back.append([span, -x - chord])
        cell_distribution.append([span, i - 1])

        profile_merge.append([span, line[8]])
        ballooning_merge.append([span, line[9]])

        span_last = span

    def symmetric_fit(data: list[list[float]], bspline: bool=True) -> SymmetricCurveType:
        line = euklid.vector.PolyLine2D(data)
        #not_from_center = int(data[0][0] == 0)
        #mirrored = [[-p[0], p[1]] for p in data[not_from_center:]][::-1] + data
        if bspline:
            return euklid.spline.SymmetricBSplineCurve.fit(line, 3)  # type: ignore
        else:
            return euklid.spline.SymmetricBezierCurve.fit(line, 3)  # type: ignore

    has_center_cell = not front[0][0] == 0
    cell_no = (len(front) - 1) * 2 + has_center_cell

    start = (2 - has_center_cell) / cell_no

    const_arr = [0.] + linspace(start, 1, len(front) - (not has_center_cell))
    rib_pos = [0.] + [p[0] for p in front[not has_center_cell:]]
    rib_pos_int = euklid.vector.Interpolation(list(zip(rib_pos, const_arr)))
    rib_distribution = euklid.vector.PolyLine2D([[i, rib_pos_int.get_value(i)] for i in linspace(0, rib_pos[-1], 30)])

    rib_distribution_curve: euklid.spline.BSplineCurve = euklid.spline.BSplineCurve.fit(rib_distribution, 3)  # type: ignore

    parametric_shape = ParametricShape(
        symmetric_fit(front),
        symmetric_fit(back),
        rib_distribution_curve,
        cell_no,
        config=config
        )
    arc_curve = ArcCurve(symmetric_fit(arc))

    return Geometry(
        shape=parametric_shape,
        arc=arc_curve,
        aoa=symmetric_fit(aoa),
        profile_merge_curve=symmetric_fit(profile_merge, bspline=True),
        ballooning_merge_curve=symmetric_fit(ballooning_merge, bspline=True)
    )


def get_geometry_parametric(table: Table, cell_num: int, config: ParametricGliderConfig) -> Geometry:
    data = {}
    curve_types = {
        "front": euklid.spline.SymmetricBSplineCurve,
        "back": euklid.spline.SymmetricBSplineCurve,
        "rib_distribution": euklid.spline.BezierCurve,
        "arc": euklid.spline.SymmetricBSplineCurve,
        "aoa": euklid.spline.SymmetricBSplineCurve,
        "profile_merge_curve": euklid.spline.SymmetricBSplineCurve,
        "ballooning_merge_curve": euklid.spline.SymmetricBSplineCurve
    }

    for column in range(0, table.num_columns, 2):
        key = table[0, column]
        if key not in curve_types:
            if key == "zrot":
                continue
            raise ValueError("Invalid curve: {key}")
        points = []
        
        if table[0, column+1] is not None:
            curve_type = getattr(euklid.spline, table[0, column+1])
        else:
            logger.warning(f"default curve for {key}")
            curve_type = curve_types[key]

        for row in range(1, table.num_rows):
            if table[row, column] is not None:
                points.append([table[row, column], table[row, column+1]])
        
        data[key] = curve_type(points)
        

    parametric_shape = ParametricShape(
        data.pop("front"),
        data.pop("back"),
        data.pop("rib_distribution"),
        cell_num,
        config=config
    )

    arc_curve = ArcCurve(data.pop("arc"))

    return Geometry(
        shape=parametric_shape,
        arc=arc_curve,
        **data
    )
