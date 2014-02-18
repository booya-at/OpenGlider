import math
from dxfwrite import DXFEngine as dxf, DXFList, DXFEngine
import openglider.Vector.projection
from openglider.glider.cells import Cell
from .cuts import cuts


def flattened_cell(cell=Cell()):
    left, right = openglider.Vector.projection.flatten_list(cell.rib1.profile_3d, cell.rib2.profile_3d)
    ballooning_left = [cell.rib1.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    ballooning_right = [cell.rib2.ballooning[x] for x in cell.rib2.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i]-left[i]
        left.data[i] -= diff * ballooning_left[i]
        right.data[i] += diff * ballooning_right[i]
    return left, right


def flatten_glider(glider, path):
    # Temporary declarations:
    allowance_general = 0.01
    glider.recalc()
    parts = []

    drawing = dxf.drawing(path)
    drawing.add_layer('MARKS')
    drawing.add_layer('CUTS')

    for cell in glider.cells:
        left, right = flattened_cell(cell)

        left_out = left.copy()
        right_out = right.copy()
        left_out.add_stuff(-allowance_general)
        right_out.add_stuff(allowance_general)

        right_out.data = right_out.data[::-1]
        left_out += right_out
        right.data = right.data[::-1]
        left = left + right

        left.layer = 'MARKS'
        left_out.layer = 'CUTS'

        parts.append([left, left_out])

    startx = 0
    for liste in parts:
        startpoint = [startx+0.1, 0]
        group = DXFList()
        for element in liste:
            startx = max(startx, startpoint[0]+max([x[0] for x in element.data]))
            group.append(dxf.polyline(points=(element.data+startpoint)*1000, layer=element.layer))
        drawing.add(group)
    drawing.save()
    return True


