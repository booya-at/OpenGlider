import euklid

from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.vector.drawing import PlotPart


class LinePlan(ShapePlot):
    def insert_lines(self):
        self.insert_design()
        self.insert_design(left=True)
        self.insert_attachment_points(True)
        self.insert_attachment_points(True, left=True)

        lower = self.glider_2d.lineset.get_lower_attachment_points()

        def all_upper_lines(node):
            lines = []
            for line in self.glider_2d.lineset.get_upper_connected_lines(node):
                lines.append(line)
                lines += all_upper_lines(line.upper_node)
            
            return lines

        for i, node in enumerate(lower):
            left = i % 2

            for line in all_upper_lines(node):
                pp = PlotPart()
                layer = pp.layers["line_"+line.layer]
                line = euklid.vector.PolyLine2D([
                        line.lower_node.get_2D(self.glider_2d.shape),
                        line.upper_node.get_2D(self.glider_2d.shape)
                    ])
                if left:
                    line = line.scale([-1, 1])

                layer += [line]
                self.drawing.parts.append(pp)

        return self
