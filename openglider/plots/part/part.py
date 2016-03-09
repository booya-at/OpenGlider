import copy

import numpy

class Layer(object):
    stroke = "black"
    stroke_width = 1

    def __init__(self, polylines=None):
        self.data = polylines or []

    def append(self, x):
        self.data.append(x)

    def copy(self):
        return Layer([p.copy() for p in self])

    def __iadd__(self, other):
        self.data += other

    def __add__(self, other):
        new = self.copy()
        new += other
        return new






class Layers(object):
    def __init__(self, **layers):
        self.layers = layers

    def __repr__(self):
        """pretty-print"""
        lines = ["Layers:"] + ["{} ({})".format(layer_name, len(layer)) for layer_name, layer in self.layers.items()]
        return "\n  - ".join(lines)

    def __getitem__(self, item):
        item = str(item)
        if item in ("name", "material_code"):
            raise ValueError()
        if not item in self.layers:
            self.layers[item] = Layer()
        return self.layers[item]

    def __setitem__(self, key, value):
        key = str(key)
        if key in ("name", "material_code"):
            raise ValueError()
        assert isinstance(value, list)
        self.layers[key].clear()
        self.layers[key] += value

    def __contains__(self, item):
        return item in self.layers

    def __iter__(self):
        for key in self.layers:
            yield str(key)

    def values(self):
        return self.layers.values()

    def items(self):
        return self.layers.items()

    def keys(self):
        return list(self)

    def copy(self):
        layer_copy = {layer_name: [line.copy() for line in layer] for layer_name, layer in self.layers.items()}
        return Layers(**layer_copy)

    def add(self, name, stroke=None, stroke_width=None):
        layer = Layer()
        if stroke is not None:
            layer.stroke = stroke

        if stroke_width is not None:
            layer.stroke_width = stroke_width

        self.layers[name] = layer
        return layer


class PlotPart(object):
    def __init__(self, cuts=None, marks=None, text=None, stitches=None, name=None, material_code="", **layers):
        self.layers = Layers()
        self.layers.add("cuts", stroke="red")
        self.layers.add("marks")
        self.layers.add("stitches")
        self.layers.add("text")

        layers.update({
            "cuts": cuts or [],
            "marks": marks or [],
            "text": text or [],
            "stitches": stitches or []
        })

        for layer_name, layer in layers.items():
            self.layers[layer_name] += layer

        self.name = name
        self.material_code = material_code

    def __json__(self):
        new = {
            "name": self.name,
            "material_code": self.material_code
        }
        new.update(self.layers)
        return new

    def copy(self):
        return copy.deepcopy(self)

    def max_function(self, axis, layer):
        start = float("-Inf")
        if layer:
            for line in layer:
                if line:
                    values = [p[axis] for p in line]
                    start = max(start, max(values))
        return start

    def min_function(self, axis, layer):
        start = float("Inf")
        if layer:
            for line in layer:
                if line:
                    values = [p[axis] for p in line]
                    start = min(start, min(values))
        return start

    @property
    def max_x(self):
        return max(self.max_function(0, l) for l in self.layers.values())

    @property
    def max_y(self):
        return max(self.max_function(1, l) for l in self.layers.values())

    @property
    def min_x(self):
        return min(self.min_function(0, l) for l in self.layers.values())

    @property
    def min_y(self):
        return min(self.min_function(1, l) for l in self.layers.values())

    @property
    def width(self):
        return self.max_x - self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    @property
    def bbox(self):
        return [[self.min_x, self.min_y], [self.max_x, self.min_y],
                [self.max_x, self.max_y], [self.min_x, self.max_y]]

    def rotate(self, angle):
        for layer in self.layers.values():
            for polyline in layer:
                polyline.rotate(angle)

    def move(self, vector):
        for layer_name, layer in self.layers.items():
            for vectorlist in layer:
                vectorlist.move(vector)

    def move_to(self, vector):
        minx = self.min_x
        miny = self.min_y
        self.move([vector[0] - minx, vector[1] - miny])

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

    def minimize_area(self):
        new_part = self.copy()
        area = new_part.area
        width = new_part.width
        height = new_part.height
        rotation = 0
        for alpha in range(1, 90):
            new_part.rotate(numpy.pi/180)
            if new_part.area < area:
                rotation = alpha
                area = new_part.area
                width = new_part.width
                height = new_part.height

        if width < height:
            rotation -= 90

        self.rotate(rotation*numpy.pi/180)
        return self

    def scale(self, factor):
        for layer in self.layers.values():
            for p in layer:
                p.scale(factor)

    def _repr_svg_(self):
        import svgwrite
        import svgwrite.container
        import svgwrite.shapes
        width = 600
        height = int(width * self.height/self.width)+1
        drawing = svgwrite.Drawing(size=["{}px".format(n) for n in (width, height)])
        drawing.viewbox(self.min_x, -self.max_y, self.width, self.height)
        group = svgwrite.container.Group()
        group.scale(1, -1)  # svg coordinate system is x->right y->down
        drawing.add(group)
        style = {
            "stroke-width": 1,
            "stroke": "black",
            "style": "vector-effect: non-scaling-stroke",
            "fill": "none"
        }

        for layer in self.layers.values():
            for line in layer:
                element = svgwrite.shapes.Polyline(line, **style)
                group.add(element)

        return drawing.tostring()

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

