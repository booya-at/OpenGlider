from openglider.plots import PlotPart
from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.vector import PolyLine2D


class DiagonalPlot(ShapePlot):
    def insert_straps(self):
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for tensionstrap in cell.straps:
                p1 = self.glider_2d.shape.get_shape_point(cell_no, tensionstrap.left)
                p2 = self.glider_2d.shape.get_shape_point(cell_no+1, tensionstrap.left)
                self.drawing.parts.append(PlotPart(marks=[PolyLine2D([p1, p2])]))

    def insert_diagonals(self):
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for diagonal in cell.diagonals:
                left = [abs(p[0]) for p in (diagonal.left_front, diagonal.left_back)]
                right = [abs(p[0]) for p in (diagonal.right_front, diagonal.right_back)]

                points_left = [self.glider_2d.shape.get_shape_point(cell_no, p) for p in left]
                points_right = [self.glider_2d.shape.get_shape_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))