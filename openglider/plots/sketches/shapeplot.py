import numpy as np

from openglider.vector import PolyLine2D
from openglider.vector.text import Text
from openglider.vector.drawing import Layout, PlotPart
import openglider.plots.marks as marks


class ShapePlot(object):
    attachment_point_mark = marks.Cross(name="attachment_point", rotation=np.pi/4)

    def __init__(self, glider_2d, glider_3d=None, drawing=None):
        super(ShapePlot, self).__init__()
        self.glider_2d = glider_2d
        self.glider_3d = glider_3d or glider_2d.get_glider_3d()
        self.drawing = drawing or Layout()

    def copy(self):
        glider2d = self.glider_2d
        glider3d = self.glider_3d
        drawing = self.drawing.copy()

        return ShapePlot(glider2d, glider3d, drawing)

    def insert_design(self, lower=True):
        part = PlotPart()
        for cell_no, cell_panels in enumerate(self.glider_2d.get_panels()):

            def match(panel):
                if lower:
                    # -> either on the left or on the right it should go further than 0
                    return panel.cut_back["left"] > 0 or panel.cut_back["right"] > 0
                else:
                    # should start before zero at least once
                    return panel.cut_front["left"] < 0 or panel.cut_front["right"] < 0

            panels = filter(match, cell_panels)
            for panel in panels:

                def get_val(val):
                    if lower:
                        return max(val, 0)
                    else:
                        return max(-val, 0)

                left_front = get_val(panel.cut_front["left"])
                rigth_front = get_val(panel.cut_front["right"])
                left_back = get_val(panel.cut_back["left"])
                right_back = get_val(panel.cut_back["right"])

                p1 = self.glider_2d.shape.get_shape_point(cell_no, left_front)
                p2 = self.glider_2d.shape.get_shape_point(cell_no, left_back)
                p3 = self.glider_2d.shape.get_shape_point(cell_no+1, right_back)
                p4 = self.glider_2d.shape.get_shape_point(cell_no+1, rigth_front)

                part.layers[panel.material_code].append(PolyLine2D([p1, p2, p3, p4, p1]))

                #self.drawing.parts.append(PlotPart(
                #    cuts=[PolyLine2D([p1, p2, p3, p4, p1])],
                #    material_code=panel.material_code))

        self.drawing.parts.append(part)

        return self

    def insert_baseline(self, pct=None):
        if pct is None:
            pct = self.glider_2d.shape.baseline_pos

        part = PlotPart()
        line = self.glider_2d.shape.get_baseline(pct)
        part.layers["marks"].append(line)
        self.drawing.parts.append(part)

    def insert_grid(self, num=11):
        import numpy as np
        part = PlotPart()

        for p in np.linspace(0, 1, num):
            line = self.glider_2d.shape.get_baseline(p)
            part.layers["marks"].append(line)

        self.drawing.parts.append(part)
        self.insert_cells()
        return self

    def insert_attachment_points(self, add_text=True):
        part = PlotPart()
        for attachment_point in self.glider_2d.lineset.get_upper_nodes():
            rib_no = attachment_point.cell_pos + attachment_point.cell_no + self.glider_2d.shape.has_center_cell

            # glider2d does not contain the mirrored rib:
            p1 = self.glider_2d.shape.get_shape_point(rib_no, attachment_point.rib_pos)
            #p2 = self.glider_2d.shape.get_shape_point(rib_no+0.02, attachment_point.rib_pos)
            
            # if rib_no == len(self.glider_2d.shape.ribs) - not(self.glider_2d.shape.has_center_cell):
            #     rib2 = rib_no - 1
            # else:
            #     rib2 = rib_no + 1
            reversed_direction = False
            rib2 = rib_no + 1
            try:
                p2 = self.glider_2d.shape.get_shape_point(rib2, attachment_point.rib_pos)
            except IndexError:
                reversed_direction = True
                rib2 = rib_no - 1
                p2 = self.glider_2d.shape.get_shape_point(rib2, attachment_point.rib_pos)

            p2[1] = p1[1]


            p1, p2 = [np.array(x) for x in (p1, p2)]

            if reversed_direction:
                p2 = p1 + (p1-p2)

            diff = (p2-p1)*0.2
            cross_left = p1 - diff
            cross_right = p1 + diff

            cross = self.attachment_point_mark(cross_left, cross_right)
            part.layers["marks"] += cross

            if add_text and attachment_point.name:
                text = Text(" {} ".format(attachment_point.name), p1, p2)
                vectors = text.get_vectors()
                part.layers["text"] += vectors

        self.drawing.parts.append(part)

    def insert_cells(self):
        cells = []
        for cell_no in range(self.glider_2d.shape.half_cell_num):
            p1 = self.glider_2d.shape.get_shape_point(cell_no, 0)
            p2 = self.glider_2d.shape.get_shape_point(cell_no+1, 0)
            p3 = self.glider_2d.shape.get_shape_point(cell_no+1, 1)
            p4 = self.glider_2d.shape.get_shape_point(cell_no, 1)
            cells.append(PolyLine2D([p1,p2,p3,p4,p1]))

        self.drawing.parts.append(PlotPart(
            marks=cells,
            material_code="cell_numbers")
        )

    def insert_cell_names(self):
        names = []
        for cell_no, cell in enumerate(self.glider_3d.cells):
            p1 = self.glider_2d.shape.get_shape_point(cell_no+0.5, 0)
            p2 = self.glider_2d.shape.get_shape_point(cell_no+0.5, 1)
            width = self.glider_2d.shape.get_shape_point(cell_no+1, 0)[0] - p1[0]

            text = Text(cell.name, p1, p2, size=width*0.8, valign=0, align="center")
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            text=names,
            material_code="cell_numbers")
        )

    def insert_rib_numbers(self):
        midrib = self.glider_2d.shape.has_center_cell
        names = []
        for rib_no, rib in enumerate(self.glider_3d.ribs):
            rib_no = max(0, rib_no)
            p1 = self.glider_2d.shape.get_shape_point(rib_no, -0.05)
            try:
                p2 = self.glider_2d.shape.get_shape_point(rib_no + 1, 0)
            except IndexError:
                p2 = self.glider_2d.shape.get_shape_point(rib_no - 1, 0)
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

    def insert_straps(self):
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for diagonal in cell.straps:
                left = [abs(p[0]) for p in (diagonal.left_front, diagonal.left_back)]
                right = [abs(p[0]) for p in (diagonal.right_front, diagonal.right_back)]

                points_left = [self.glider_2d.shape.get_shape_point(cell_no, p) for p in left]
                points_right = [self.glider_2d.shape.get_shape_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

        return self

    def insert_diagonals(self):
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for diagonal in cell.diagonals:
                left = [abs(p[0]) for p in (diagonal.left_front, diagonal.left_back)]
                right = [abs(p[0]) for p in (diagonal.right_front, diagonal.right_back)]

                points_left = [self.glider_2d.shape.get_shape_point(cell_no, p) for p in left]
                points_right = [self.glider_2d.shape.get_shape_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

        return self

    def export_a4(self, path, add_styles=False):
        new = self.drawing.copy()
        new.scale_a4()
        return new.export_svg(path, add_styles)

    def _repr_svg_(self):
        new = self.drawing.copy()
        new.scale_a4()
        return new._repr_svg_()
