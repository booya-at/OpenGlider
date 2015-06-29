import copy
import io
import svgwrite
import svgwrite.container
import svgwrite.shapes

from openglider.plots import config
from openglider.vector.polyline import PolyLine2D


class PlotPart():
    def __init__(self, cuts=None, marks=None, text=None, name=None):
        self.cuts = cuts or []
        self.marks = marks or []
        self.text = text or []
        self.name = name

    def __json__(self):
        return {
            "cuts": self.cuts,
            "marks": self.marks,
            "text": self.text,
            "name": self.name
        }

    def copy(self):
        return copy.deepcopy(self)

    @property
    def layer_dict(self):
        # TODO: remove
        return {"CUTS": self.cuts,
                "MARKS": self.marks,
                "TEXT": self.text}

    def max_function(self, index):
        start = float("-Inf")
        for layer in self.layer_dict.values():
            if layer:
                for line in layer:
                    if line:
                        values = [p[index] for p in line]
                        start = max(start, max(values))
        return start

    def min_function(self, index):
        start = float("Inf")
        for layer_name, layer in self.layer_dict.items():
            if layer:
                for line in layer:
                    if line:
                        try:
                            values = [p[index] for p in line]
                            start = min(start, min(values))
                        except Exception as e:
                            print("fehler {}".format(line))
                            raise ValueError("{} {} {} {}".format(layer_name, layer, self.name, e))
        return start

    @property
    def max_x(self):
        return self.max_function(0)

    @property
    def max_y(self):
        return self.max_function(1)

    @property
    def min_x(self):
        return self.min_function(0)

    @property
    def min_y(self):
        return self.min_function(1)

    @property
    def width(self):
        return self.max_x -self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    @property
    def bbox(self):
        return [[self.min_x, self.min_y], [self.max_x, self.min_y],
                [self.max_x, self.max_y], [self.min_x, self.max_y]]

    def rotate(self, angle):
        for layer in self.layer_dict.values():
            for polyline in layer:
                polyline.rotate(angle)

    def move(self, vector):
        for layer in self.layer_dict.values():
            for vectorlist in layer:
                vectorlist.move(vector)

    def move_to(self, vector):
        self.move([vector[0] - self.min_x, vector[1] - self.min_y])

    def intersects(self, other):
        """
        Tells whether this parts intersects with the other part
        """
        if self.max_x < other.min_x:
            return False
        if self.min_x > other.max_x:
            return False
        if self.max_y < other.min_y:
            return False
        if self.min_y > other.max_y:
            return False
        return True

    @property
    def area(self):
        return self.width * self.height

    def return_layer_svg(self, layer, scale=1):
        """
        Return a layer scaled for svg_coordinate_system [x,y = (mm, -mm)]
        """
        if layer in self.layer_dict:
            new = []
            for line in self.layer_dict[layer]:
                new.append(map(lambda point: point * [scale, -scale], line))
            return new
        else:
            return None


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
                if layer_name in part.layer_dict:
                    lines = part.return_layer_svg(layer_name, scale=config["scale"])
                    for line in lines:
                        element = svgwrite.shapes.Polyline(line, **layer_config)
                        part_group.add(element)

            group.add(part_group)

        return group

    def _repr_svg_(self):
        strio = io.StringIO()
        drawing = svgwrite.Drawing()
        group = self.get_svg_group()

        scale = 0.75/self.width
        group.scale(scale)
        group.translate(tx=-self.min_x*1000, ty=self.max_y*1000)
        drawing.add(group)
        drawing.viewbox(0, 0, self.width*scale*1000, self.height*scale*1000)
        drawing.write(strio)
        strio.seek(0)
        return strio.read()


def create_svg(drawing_area, path):
    drawing = svgwrite.Drawing()
    outer_group = svgwrite.container.Group()
    drawing.add(outer_group)
    # svg is shifted downwards
    drawing_area.move([0, -drawing_area.max_y])
    for part in drawing_area.parts:
        part_group = svgwrite.container.Group()

        for layer_name, layer_config in config.sewing_config["layers"].items():
            if layer_name in part.layer_dict:
                lines = part.return_layer_svg(layer_name, scale=config.sewing_config["scale"])
                for line in lines:
                    element = svgwrite.shapes.Polyline(line, **layer_config)
                    part_group.add(element)
        outer_group.add(part_group)

    if isinstance(path, str):
        with open(path, "w") as output_file:
            return drawing.write(output_file)
    else:
        return drawing.write(path)

        # FLATTENING
        # Dict for layers
        # Flatten all cell-parts
        #   * attachment points
        #   * miniribs
        #   * sewing marks
        # FLATTEN RIBS
        #   * airfoil
        #   * attachment points
        #   * gibus arcs
        #   * holes
        #   * rigidfoils
        #   * sewing marks
        #   ---> SCALE
        # FLATTEN DIAGONALS
        #     * Flatten + add stuff
        #     * Draw marks on ribs

    from IPython.display import SVG