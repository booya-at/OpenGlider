from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.vector.drawing import PlotPart
from openglider.vector import PolyLine2D


class LinePlan(ShapePlot):
    def insert_lines(self):
        self.insert_design()
        self.insert_attachment_points(True)
        for line in self.glider_2d.lineset.lines:
            pp = PlotPart()
            layer = pp.layers["line_"+line.layer]
            layer += [PolyLine2D([
                    line.lower_node.get_2D(self.glider_2d.shape),
                    line.upper_node.get_2D(self.glider_2d.shape)
                ])]
            self.drawing.parts.append(pp)

        return self
