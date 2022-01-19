from typing import TYPE_CHECKING, List
import logging
import math
import numbers
import re

import euklid
import pyfoil
from openglider.glider.ballooning import BallooningBezier, BallooningBezierNeu
from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.lines import LineSet2D, LowerNode2D
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.table import GliderTables
from openglider.glider.parametric.table.data_table import DataTable
from openglider.glider.parametric.table.material import CellClothTable, RibClothTable
from openglider.glider.parametric.table.cell.ballooning import BallooningTable
from openglider.glider.parametric.table.cell.cuts import CutTable
from openglider.glider.parametric.table.cell.diagonals import DiagonalTable, StrapTable
from openglider.glider.parametric.table.cell.miniribs import MiniRibTable
from openglider.glider.parametric.table.curve import CurveTable
from openglider.glider.parametric.table.rib.profile import ProfileTable
from openglider.glider.parametric.table.rib.holes import HolesTable
from openglider.glider.parametric.table.rib.rib import SingleSkinTable
from openglider.glider.parametric.table.rigidfoil import RibRigidTable, CellRigidTable
from openglider.glider.parametric.table.attachment_points import CellAttachmentPointTable, AttachmentPointTable
from openglider.utils import linspace
from openglider.utils.table import Table

if TYPE_CHECKING:
    from openglider.glider.parametric import ParametricGlider

logger = logging.getLogger(__name__)

def import_ods_2d(Glider2D, filename) -> "ParametricGlider":
    logger.info(f"Import file: {filename}")
    tables = Table.load(filename)

    return import_ods_glider(tables)
    
def import_ods_glider(tables: List[Table]) -> "ParametricGlider":
    from openglider.glider.parametric import ParametricGlider
    cell_sheet = tables[1]
    rib_sheet = tables[2]

    # file-version
    file_version_match = re.match(r"V([0-9]*)", str(cell_sheet["A1"]))
    if file_version_match:
        file_version = int(file_version_match.group(1))
    else:
        file_version = 1
    logger.info(f"Loading file version {file_version}")
    # ------------

    # profiles = [BezierProfile2D(profile) for profile in transpose_columns(sheets[3])]
    profiles = [pyfoil.Airfoil(profile, name).normalized() for name, profile in transpose_columns(tables[3])]

    if file_version > 2:
        has_center_cell = not tables[0]["C2"] == 0
        cell_no = (tables[0].num_rows - 2) * 2 + has_center_cell
        geometry = get_geometry_parametric(tables[5], cell_no)
    else:
        geometry = get_geometry_explicit(tables[0])
        has_center_cell = geometry["shape"].has_center_cell

    balloonings = []
    for i, (name, baloon) in enumerate(transpose_columns(tables[4])):
        ballooning_type = (tables[4][0, 2*i+1] or "").upper()
        if baloon:
            if ballooning_type == "V1":
                i = 0
                while baloon[i + 1][0] > baloon[i][0]:
                    i += 1

                upper = baloon[:i + 1]
                lower = [(x, -y) for x, y in baloon[i + 1:]]

                ballooning = BallooningBezier(upper, lower, name=name)
                balloonings.append(BallooningBezierNeu.from_classic(ballooning))

            elif ballooning_type == "V2":
                i = 0
                while baloon[i + 1][0] > baloon[i][0]:
                    i += 1

                upper = baloon[:i + 1]
                lower = baloon[i + 1:]

                ballooning = BallooningBezier(upper, lower, name=name)
                balloonings.append(BallooningBezierNeu.from_classic(ballooning))

            elif ballooning_type == "V3":
                balloonings.append(BallooningBezierNeu(baloon))

            else:
                raise ValueError("No ballooning type specified")

    data_dct = DataTable(tables[7]).get_dct()

    # set stabi cell
    if data_dct.pop("STABICELL", None):
        shape = geometry["shape"]
        if not hasattr(shape, "stabi_cell"):
            raise Exception(f"Cannot add stabi cell on {geometry['shape']}")
        
        shape.stabi_cell = True

    if len(tables) > 8:
        curves_table = tables[8]
    else:
        curves_table = Table()
    
    curves = CurveTable(curves_table)

    add_rib = geometry["shape"].has_center_cell and data_dct.get("version", "0.0.1") >= "0.1.0"

    attachment_points = LineSet2D.read_attachment_point_table(
        cell_table=cell_sheet,
        rib_table=rib_sheet,
        cell_no=geometry["shape"].cell_num,
        curves=curves.get_curves(geometry["shape"].get_half_shape()),
        add_center_rib=add_rib
    )

    attachment_points = {n.name: n for n in attachment_points}

    attachment_points_lower = get_lower_aufhaengepunkte(data_dct)

    # RIB HOLES
    rib_holes = HolesTable(rib_sheet)
    rigidfoils = RibRigidTable(rib_sheet)
    cell_rigidfoils = CellRigidTable(cell_sheet)
    cuts = CutTable(cell_sheet)

    # Diagonals: center_left, center_right, width_l, width_r, height_l, height_r
    diagonals = DiagonalTable(cell_sheet, file_version)
    straps = StrapTable(cell_sheet)

    miniribs = MiniRibTable(cell_sheet)

    lineset_table = tables[6]
    lineset = LineSet2D.read_input_table(lineset_table, attachment_points_lower, attachment_points)
    lineset.set_default_nodes2d_pos(geometry["shape"])
    lineset.trim_corrections = {
        name: value for name, value in data_dct.pop("trim_correction", [])
    }

    ballooning_factors = BallooningTable(cell_sheet)
    skin_ribs = SingleSkinTable(rib_sheet)

    glider_tables = GliderTables()
    glider_tables.cuts = cuts
    glider_tables.ballooning_factors = ballooning_factors
    glider_tables.holes = rib_holes
    glider_tables.diagonals = diagonals
    glider_tables.rigidfoils_rib = rigidfoils
    glider_tables.rigidfoils_cell = cell_rigidfoils
    glider_tables.straps = straps
    glider_tables.material_cells = CellClothTable(cell_sheet)
    glider_tables.material_ribs = RibClothTable(rib_sheet)
    glider_tables.miniribs = miniribs
    glider_tables.rib_modifiers = skin_ribs
    glider_tables.profiles = ProfileTable(rib_sheet)
    glider_tables.attachment_points_rib = AttachmentPointTable(rib_sheet)
    glider_tables.attachment_points_cell = CellAttachmentPointTable(cell_sheet)
    
    glider_2d = ParametricGlider(tables=glider_tables,
                         curves=curves,
                         profiles=profiles,
                         balloonings=balloonings,
                         lineset=lineset,
                         speed=data_dct.pop("SPEED"),
                         glide=data_dct.pop("GLIDE"),
                         **geometry)
    
    if len(data_dct) > 0:
        logger.error(f"Unknown data keys: {list(data_dct.keys())}")


    return glider_2d


def get_geometry_explicit(sheet: Table):
    # All Lists
    front = []
    back = []
    cell_distribution = []
    aoa = []
    arc = []
    profile_merge = []
    ballooning_merge = []
    zrot = []

    y = z = span_last = alpha = 0.
    for i in range(1, sheet.num_rows):
        line = [sheet[i, j] for j in range(sheet.num_columns)]
        if not line[0]:
            break  # skip empty line
        if not all(isinstance(c, numbers.Number) for c in line[:10]):
            raise ValueError("Invalid row ({}): {}".format(i, line))
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

        zrot.append([span, line[7] * math.pi / 180])

        span_last = span

    def symmetric_fit(data: List[List[float]], bspline=True):
        line = euklid.vector.PolyLine2D(data)
        #not_from_center = int(data[0][0] == 0)
        #mirrored = [[-p[0], p[1]] for p in data[not_from_center:]][::-1] + data
        if bspline:
            return euklid.spline.SymmetricBSplineCurve.fit(line, 3)
        else:
            return euklid.spline.SymmetricBezierCurve.fit(line, 3)

    has_center_cell = not front[0][0] == 0
    cell_no = (len(front) - 1) * 2 + has_center_cell

    start = (2 - has_center_cell) / cell_no

    const_arr = [0.] + linspace(start, 1, len(front) - (not has_center_cell))
    rib_pos = [0.] + [p[0] for p in front[not has_center_cell:]]
    rib_pos_int = euklid.vector.Interpolation(list(zip(rib_pos, const_arr)))
    rib_distribution = euklid.vector.PolyLine2D([[i, rib_pos_int.get_value(i)] for i in linspace(0, rib_pos[-1], 30)])

    rib_distribution_curve: euklid.spline.BSplineCurve = euklid.spline.BSplineCurve.fit(rib_distribution, 3)

    parametric_shape = ParametricShape(symmetric_fit(front), symmetric_fit(back), rib_distribution_curve, cell_no)
    arc_curve = ArcCurve(symmetric_fit(arc))

    return {
        "shape": parametric_shape,
        "arc": arc_curve,
        "aoa": symmetric_fit(aoa),
        "zrot": symmetric_fit(zrot),
        "profile_merge_curve": symmetric_fit(profile_merge, bspline=True),
        "ballooning_merge_curve": symmetric_fit(ballooning_merge, bspline=True)
    }


def get_geometry_parametric(table: Table, cell_num):
    data = {}
    curve_types = {
        "front": euklid.spline.SymmetricBSplineCurve,
        "back": euklid.spline.SymmetricBSplineCurve,
        "rib_distribution": euklid.spline.BezierCurve,
        "arc": euklid.spline.SymmetricBSplineCurve,
        "aoa": euklid.spline.SymmetricBSplineCurve,
        "zrot": euklid.spline.SymmetricBSplineCurve,
        "profile_merge_curve": euklid.spline.SymmetricBSplineCurve,
        "ballooning_merge_curve": euklid.spline.SymmetricBSplineCurve
    }

    for column in range(0, table.num_columns, 2):
        key = table[0, column]
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
        data["front"], data["back"], data["rib_distribution"], cell_num
    )

    arc_curve = ArcCurve(data["arc"])

    return {
        "shape": parametric_shape,
        "arc": arc_curve,
        "aoa": data["aoa"],
        "zrot": data["zrot"],
        "profile_merge_curve": data["profile_merge_curve"],
        "ballooning_merge_curve": data["ballooning_merge_curve"]
    }

def get_lower_aufhaengepunkte(data):
    aufhaengepunkte = {}

    axis_to_index = {"X": 0, "Y": 1, "Z": 2}
    regex = re.compile("AHP([XYZ])(.*)")

    keys_to_remove = []

    for key in data:
        if isinstance(key, str):
            match = regex.match(key)
            if match:
                axis, name = match.groups()

                aufhaengepunkte.setdefault(name, [0, 0, 0])
                aufhaengepunkte[name][axis_to_index[axis]] = data[key]
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        data.pop(key)

    return {name: LowerNode2D([0, 0], euklid.vector.Vector3D(position), name)
            for name, position in aufhaengepunkte.items()}


def transpose_columns(sheet: Table, columnswidth=2):
    num_columns = sheet.num_columns
    num_elems = num_columns // columnswidth
    # if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(num_elems):
        first_column = col * columnswidth
        last_column = (col + 1) * columnswidth
        columns = range(first_column, last_column)
        name = sheet[0, first_column]
        if not isinstance(name, numbers.Number):  # py2/3: str!=unicode
            start = 1
        else:
            name = "unnamed"
            start = 0

        element = []

        for i in range(start, sheet.num_rows):
            row = [sheet[i, j] for j in columns]
            if all([j is None for j in row]):  # Break at empty line
                break
            if not all([isinstance(j, numbers.Number) for j in row]):
                raise ValueError("Invalid value at row {}: {}".format(i, row))
            element.append(row)
        result.append((name, element))
    return result
