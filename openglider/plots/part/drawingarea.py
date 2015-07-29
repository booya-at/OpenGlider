import io
import svgwrite
import svgwrite.container
import svgwrite.shapes

from openglider.plots import config

__author__ = 'simon'


class DrawingArea():
    def __init__(self, parts=None):
        self.parts = parts or []

    def __json__(self):
        return {"parts": self.parts}

    @classmethod
    def create_raster(cls, parts, distance_x=0.2, distance_y=0.1):
        area = cls()
        last_x = 0.
        last_y = 0.
        next_x = [0.]
        for col in parts:
            for part in col:
                part.move([last_x - part.min_x, last_y - part.min_y])
                area.parts.append(part)
                last_y = part.max_y + distance_y
                next_x.append(part.max_x)
            last_x = max(next_x) + distance_x
            last_y = 0.

        return area

    @property
    def min_x(self):
        return min([part.min_x for part in self.parts])

    @property
    def max_x(self):
        return max([part.max_x for part in self.parts])

    @property
    def min_y(self):
        return min([part.min_y for part in self.parts])

    @property
    def max_y(self):
        return max([part.max_y for part in self.parts])

    @property
    def bbox(self):
        return [[self.min_x, self.min_y], [self.max_x, self.min_y],
                [self.max_x, self.max_y], [self.min_x, self.max_y]]

    @property
    def width(self):
        return abs(self.max_x - self.min_x)

    @property
    def height(self):
        return abs(self.max_y - self.min_y)

    def move(self, vector):
        for part in self.parts:
            part.move(vector)

    def join(self, other, position=None):
        assert isinstance(other, DrawingArea)

        if self.parts:
            x0 = self.max_x + 0.2
        else:
            x0 = 0
        x = x0 - other.min_x
        y = 0 - other.min_y
        other.move([x, y])
        self.parts += other.parts

    def get_svg_group(self, config=config.sewing_config):
        group = svgwrite.container.Group()

        for part in self.parts:
            part_group = svgwrite.container.Group()

            for layer_name, layer_config in config["layers"].items():
                if layer_name in part.layers:
                    lines = part.return_layer_svg(layer_name, scale=config["scale"])
                    for line in lines:
                        element = svgwrite.shapes.Polyline(line, **layer_config)
                        part_group.add(element)

            group.add(part_group)

        return group

    def get_svg_drawing(self):
        width, height = self.width, self.height
        drawing = svgwrite.Drawing(size=["{}mm".format(n) for n in (width, height)])
        drawing.viewbox(self.min_x, self.min_y, self.width, self.height)
        group = self.get_svg_group()
        drawing.add(group)
        return drawing

    def _repr_svg_(self):
        drawing = self.get_svg_drawing()
        return drawing.tostring()

    def export_svg(self, path):
        drawing = self.get_svg_drawing()
        with open(path, "w") as outfile:
            drawing.write(outfile)

    def export_dxf(self, path):
        import ezdxf
        drawing = ezdxf.new(dxfversion="ac1015")
        ms = drawing.modelspace()

        for part in self.parts:
            group = drawing.groups.add()
            with group.edit_data() as part_group:
                for layer_name, layer in part.layers.items():
                    if layer_name not in drawing.layers:
                        drawing.layers.create(name=layer_name)

                    for elem in layer:
                        pl = ms.add_lwpolyline(elem, dxfattribs={"layer": layer_name})
                        part_group.append(pl)

        drawing.saveas(path)
        return drawing