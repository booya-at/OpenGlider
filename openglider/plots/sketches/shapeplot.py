import numpy

from openglider.plots import DrawingArea, PlotPart
from openglider.vector import PolyLine2D


class ShapePlot(DrawingArea):
    def __init__(self, glider_2d, glider_3d=None):
        super(ShapePlot, self).__init__()
        self.glider_2d = glider_2d
        self.glider_3d = glider_3d or glider_2d.get_glider_3d()

    def insert_design(self, lower=True):
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

                self.parts.append(PlotPart(
                    cuts=[PolyLine2D([p1, p2, p3, p4, p1])],
                    material_code=panel.material_code))

        return self

    def insert_vectorstraps(self):
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for tensionstrap in cell.straps:
                p1 = self.glider_2d.shape.get_shape_point(cell_no, tensionstrap.left)
                p2 = self.glider_2d.shape.get_shape_point(cell_no+1, tensionstrap.left)
                strap = PlotPart(marks=[PolyLine2D([p1, p2])])
                self.parts.append(strap)

        return self

    def insert_attachment_points(self):
        for attachment_point in self.glider_2d.lineset.get_upper_nodes():
            center = self.glider_2d.shape.get_shape_point(attachment_point.rib_no, attachment_point.rib_pos)
            if attachment_point.rib_no == len(self.glider_2d.shape.ribs)-1:
                left = True
                rib2 = attachment_point.rib_no - 1
            else:
                left = False
                rib2 = attachment_point.rib_no + 1

            p2 = numpy.array(self.glider_2d.shape.get_shape_point(rib2, attachment_point.rib_pos))
            p2[1] = center[1]

            center, p2 = [numpy.array(x) for x in (center, p2)]

            diff = (p2-center)*0.2
            cross_left = center - diff
            cross_right = center + diff
            import openglider.plots.marks as marks
            cross = marks.cross(cross_left, cross_right, numpy.pi/4)

            self.parts.append(PlotPart(marks=cross))