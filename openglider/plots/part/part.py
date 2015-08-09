import copy

class PlotPart():
    def __init__(self, cuts=None, marks=None, text=None, name=None, material_code=""):
        self.cuts = cuts or []
        self.marks = marks or []
        self.text = text or []
        self.name = name
        self.material_code = material_code

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
    def layers(self):
        return {"Cuts": self.cuts,
                "Marks": self.marks,
                "Text": self.text}

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
        for layer in self.layers.values():
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
        if layer in self.layers:
            new = []
            for line in self.layers[layer]:
                new.append(map(lambda point: point * [scale, -scale], line))
            return new
        else:
            return None

    def scale(self, factor):
        for layer in self.layers.values():
            for p in layer:
                p.scale(factor)

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

