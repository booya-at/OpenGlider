from typing import List

import numpy as np
import euklid

from openglider.glider import GliderProject
from openglider.vector.text import Text
from openglider.vector.drawing import Layout, PlotPart
import openglider.plots.marks as marks
from openglider.glider.cell.elements import Panel


class ShapePlot(object):
    project: GliderProject
    attachment_point_mark = marks.Cross(name="attachment_point", rotation=np.pi/4)

    def __init__(self, project: GliderProject, drawing=None):
        super(ShapePlot, self).__init__()
        self.project = project
        self.glider_2d = project.glider
        self.glider_3d = project.glider_3d
        self.drawing = drawing or Layout()

        self.shape_r = self.glider_2d.shape.get_half_shape()
        self.shape_l = self.shape_r.copy().scale(x=-1)
        self.shapes = [self.shape_r, self.shape_l]

    def copy(self):
        drawing = self.drawing.copy()

        return ShapePlot(self.project, drawing)

    def _rib_range(self, left):
        start = 0
        end = self.project.glider.shape.half_cell_num
        if self.glider_2d.shape.has_center_cell and left:
            start = 1

        return range(start, end+1)

    
    def _cell_range(self, left):
        start = 0
        end = self.project.glider.shape.half_cell_num
        if self.glider_2d.shape.has_center_cell and left:
            start = 1

        return range(start, end)

    def insert_design(self, lower=True, left=False):
        shape = self.shapes[left]

        part = PlotPart()
        panels = self.glider_2d.get_panels()

        for cell_no in self._cell_range(left):
            cell_panels = panels[cell_no]

            def match(panel):
                if lower:
                    # -> either on the left or on the right it should go further than 0
                    return panel.cut_back["left"] > 0 or panel.cut_back["right"] > 0
                else:
                    # should start before zero at least once
                    return panel.cut_front["left"] < 0 or panel.cut_front["right"] < 0

            cell_side_panels: List[Panel] = filter(match, cell_panels)

            for panel in cell_side_panels:

                def get_val(val):
                    if lower:
                        return max(val, 0)
                    else:
                        return max(-val, 0)

                left_front = get_val(panel.cut_front["left"])
                rigth_front = get_val(panel.cut_front["right"])
                left_back = get_val(panel.cut_back["left"])
                right_back = get_val(panel.cut_back["right"])

                p1 = shape.get_point(cell_no, left_front)
                p2 = shape.get_point(cell_no, left_back)
                p3 = shape.get_point(cell_no+1, right_back)
                p4 = shape.get_point(cell_no+1, rigth_front)

                part.layers[str(panel.material)].append(
                    euklid.vector.PolyLine2D([p1, p2, p3, p4, p1])
                    )

                self.drawing.parts.append(PlotPart(
                    cuts=[euklid.vector.PolyLine2D([p1, p2, p3, p4, p1])],
                    material_code=f"{panel.material}#{panel.material.color_code}"))

        #self.drawing.parts.append(part)

        return self

    def insert_baseline(self, pct=None, left=False):
        shape = self.shapes[left]

        if pct is None:
            pct = self.glider_2d.shape.baseline_pos

        part = PlotPart()
        
        line = euklid.vector.PolyLine2D([shape.get_point(rib, pct) for rib in self._rib_range(left)])
        part.layers["marks"].append(line)
        self.drawing.parts.append(part)

    def insert_grid(self, num=11, left=False):
        import numpy as np
        part = PlotPart()

        for x in np.linspace(0, 1, num):
            self.insert_baseline(x, left=left)

        self.insert_cells(left=left)
        return self

    def insert_attachment_points(self, add_text=True, left=False):
        shape = self.shapes[left]

        part = PlotPart()
        for attachment_point in self.glider_2d.lineset.get_upper_nodes():
            rib_no = attachment_point.cell_pos + attachment_point.cell_no + self.glider_2d.shape.has_center_cell

            # glider2d does not contain the mirrored rib:
            p1 = shape.get_point(rib_no, attachment_point.rib_pos)
            p2 = p1 + [0.2, 0]


            diff = (p2-p1)*0.2
            cross_left = p1 - diff
            cross_right = p1 + diff

            cross = self.attachment_point_mark(cross_left, cross_right)
            part.layers["marks"] += cross

            if add_text and attachment_point.name:
                p1 = p1 + [0, 0.02]
                p2 = p2 + [0, 0.02]
                text = Text(" {} ".format(attachment_point.name), p1, p2)
                vectors = text.get_vectors()
                part.layers["text"] += vectors

        self.drawing.parts.append(part)

    def insert_cells(self, left=False):
        shape = self.shapes[left]

        cells = []

        for cell_no in self._cell_range(left):
            p1 = shape.get_point(cell_no, 0)
            p2 = shape.get_point(cell_no+1, 0)
            p3 = shape.get_point(cell_no+1, 1)
            p4 = shape.get_point(cell_no, 1)
            cells.append(euklid.vector.PolyLine2D([p1,p2,p3,p4,p1]))

        self.drawing.parts.append(PlotPart(
            marks=cells,
            material_code="cell_numbers")
        )

    def insert_cell_names(self, left=False):
        shape = self.shapes[left]
        names = []
        
        for cell_no in self._cell_range(left):
            cell = self.glider_3d.cells[cell_no]
            p1 = shape.get_point(cell_no+0.5, 0)
            p2 = shape.get_point(cell_no+0.5, 1)
            width = shape.get_point(cell_no+1, 0)[0] - p1[0]

            text = Text(cell.name, p1, p2, size=width*0.8, valign=0, align="center")
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            text=names,
            material_code="cell_numbers")
        )

    def insert_rib_numbers(self, left=False):
        shape = self.shapes[left]
        midrib = self.glider_2d.shape.has_center_cell
        names = []

        for rib_no in self._rib_range(left):
            rib = self.glider_3d.ribs[rib_no]
            rib_no = max(0, rib_no)
            p1 = shape.get_point(rib_no, -0.05)
            try:
                p2 = shape.get_point(rib_no + 1, 0)
            except IndexError:
                p2 = shape.get_point(rib_no - 1, 0)
            diff = abs(p1[0]- p2[0]) # cell distance
            p2[0] = p1[0]
            p2[1] = p1[1] + diff

            # notwendig?
            # if rib_no == 0 and midrib:
            #     p1[0] = -p1[0]
            #     p2[0] = -p2[0]
            #     continue

            text = Text(rib.name, p1, p2, valign=0)
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            text=names,
            material_code="rib_numbers")
        )

    def insert_straps(self, left=False):
        shape = self.shapes[left]

        for cell_no in self._cell_range(left):
            cell = self.glider_3d.cells[cell_no]
            for diagonal in cell.straps:
                left = [abs(p[0]) for p in (diagonal.left_front, diagonal.left_back)]
                right = [abs(p[0]) for p in (diagonal.right_front, diagonal.right_back)]

                points_left = [shape.get_point(cell_no, p) for p in left]
                points_right = [shape.get_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[euklid.vector.PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

        return self

    def insert_diagonals(self, left=False):
        shape = self.shapes[left]

        for cell_no in self._cell_range(left):
            cell = self.glider_3d.cells[cell_no]
            for diagonal in cell.diagonals:
                left = [abs(p[0]) for p in (diagonal.left_front, diagonal.left_back)]
                right = [abs(p[0]) for p in (diagonal.right_front, diagonal.right_back)]

                points_left = [shape.get_point(cell_no, p) for p in left]
                points_right = [shape.get_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[euklid.vector.PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

        return self

    def export_a4(self, path, fill=False):
        new = self.drawing.copy()
        new.scale_a4()
        return new.export_svg(path, fill=fill)

    def _repr_svg_(self):
        new = self.drawing.copy()
        new.scale_a4()
        return new._repr_svg_()
