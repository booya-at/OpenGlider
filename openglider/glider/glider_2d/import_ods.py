import ezodf
import numpy

from openglider.airfoil import Profile2D
from openglider.glider.ballooning import BallooningBezier
from openglider.glider.glider_2d import UpperNode2D
from openglider.lines import Node, Line, LineSet


def import_ods_2d(cls, filename):
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets
    profiles = [Profile2D(profile) for profile in transpose_columns(sheets[3])]

    balloonings_temp = transpose_columns(sheets[4])
    balloonings = []
    for baloon in balloonings_temp:
        upper = [[0, 0]] + baloon[:7] + [[1, 0]]
        lower = [[0, 0]] + [[i[0], -1 * i[1]] for i in baloon[8:15]] + [[1, 0]]
        balloonings.append(BallooningBezier([upper, lower]))

    data = {}
    datasheet = sheets[-1]
    assert isinstance(datasheet, ezodf.Sheet)
    for i in range(datasheet.nrows()):
        data[datasheet.get_cell([i, 0]).value] = datasheet.get_cell([i, 1]).value

    glide = data["GLEITZAHL"]

    front = []
    back = []
    cell_distribution = []
    aoa = []
    arc = []
    profile_merge = []
    ballooning_merge = []

    main = sheets[0]
    x = y = z = span_last = alpha = 0.

    for i in range(1, main.nrows()):
        line = [main.get_cell([i, j]).value for j in range(main.ncols())]
        if not line[0]:
            break  # skip empty line

        chord = line[1]  # Rib-Chord
        span = line[2]  # spanwise-length (flat)
        x = line[3]  # x-value -> front/back (ribwise)
        y += numpy.cos(alpha) * (span - span_last)  # y-value -> spanwise
        z -= numpy.sin(alpha) * (span - span_last)  # z-axis -> up/down

        aoa.append([y,line[5] * numpy.pi / 180])
        arc.append([y, z])
        front.append([y,-x])
        back.append([y,-x-chord])
        cell_distribution.append([y,i-1])

        profile_merge.append(line[8])
        ballooning_merge.append(line[9])

        zrot = line[7] * numpy.pi / 180

        alpha += line[4] * numpy.pi / 180  # angle after the rib
        span_last = span

    attachment_points = [UpperNode2D(args[0], args[1], args[2]) for args in read_elements(sheets[2], "AHP", len_data=2)]
    attachment_points.sort(key=lambda element: element.number)
    #attachment_points_lower = get_lower_aufhaengepunkte(glider.data)

    for p in attachment_points:
        p.force = numpy.array([0, 0, 10])
        p.get_position()

    #glider.lineset = tolist_lines(sheets[6], attachment_points_lower, attachment_points)
    #glider.lineset.calc_geo()
    #glider.lineset.calc_sag()

    return cls()



def get_lower_aufhaengepunkte(data):
    aufhaengepunkte = {}
    xyz = {"X": 0, "Y": 1, "Z": 2}
    for key in data:
        if not key is None and "AHP" in key:
            pos = int(key[4])
            if pos not in aufhaengepunkte:
                aufhaengepunkte[pos] = [None, None, None]
            aufhaengepunkte[pos][xyz[key[3].upper()]] = data[key]
    for node in aufhaengepunkte:
        aufhaengepunkte[node] = Node(0, numpy.array(aufhaengepunkte[node]))
    return aufhaengepunkte


def transpose_columns(sheet=ezodf.Table(), columnswidth=2):
    num = sheet.ncols()
    #if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(int(num / columnswidth)):
        columns = range(col * columnswidth, (col + 1) * columnswidth)
        element = []
        i = 0
        while i < sheet.nrows():
            row = [sheet.get_cell([i, j]).value for j in columns]
            if sum([j is None for j in row]) == len(row):  # Break at empty line
                break
            i += 1
            element.append(row)
        result.append(element)
    return result


def tolist_lines(sheet, attachment_points_lower, attachment_points_upper):
    num_rows = sheet.nrows()
    num_cols = sheet.ncols()
    linelist = []
    current_nodes = [None for i in range(num_cols)]
    i = j = 0
    count = 0

    while i < num_rows:
        val = sheet.get_cell([i, j]).value
        if j == 0:  # first floor
            if val is not None:
                current_nodes = [attachment_points_lower[int(sheet.get_cell([i, j]).value)]] + \
                                [None for __ in range(num_cols)]
            j += 1
        elif j+2 < num_cols:
            if val is None:
                j += 2
            else:
                lower = current_nodes[j//2]
                #print(lower)
                if j + 4 >= num_cols or sheet.get_cell([i, j+2]).value is None:  # gallery

                    upper = attachment_points_upper[int(val-1)]
                    line_length = None
                    i += 1
                    j = 0
                else:
                    upper = Node(node_type=1)
                    current_nodes[j//2+1] = upper
                    line_length = sheet.get_cell([i, j]).value
                    j += 2
                linelist.append(
                    Line(number=count, lower_node=lower, upper_node=upper, vinf=numpy.array([10,0,0]), target_length=line_length))  #line_type=sheet.get_cell
                count += 1
                #print("made line", linelist[-1].init_length)
                #print(upper, lower)
        elif j+2 >= num_cols:
            j = 0
            i += 1

    #print(len(linelist))
    return LineSet(linelist, v_inf=numpy.array([10,0,0]))


def read_elements(sheet, keyword, len_data=2):
    """
    Return rib/cell_no for the element + data
    """
    #print("jo")
    elements = []
    j = 0
    while j < sheet.ncols():
        if sheet.get_cell([0, j]).value == keyword:
            for i in range(1, sheet.nrows()):
                line = [sheet.get_cell([i, j+k]).value for k in range(len_data)]
                if line[0] is not None:
                    elements.append([i-1] + line)
            j += len_data
        else:
            j += 1
    return elements
