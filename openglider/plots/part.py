from openglider.vector import PolyLine2D


class PlotPart():
    def __init__(self, layer_dict=None):
        self._layer_dict = {}
        self.layer_dict = layer_dict or {}

    @property
    def layer_dict(self):
        return self._layer_dict

    @layer_dict.setter
    def layer_dict(self, layer_dict):
        assert isinstance(layer_dict, dict)
        for layer in layer_dict.iteritems():
            if not isinstance(layer, PolyLine2D):
                layer = PolyLine2D(layer)
        self._layer_dict = layer_dict

    def __getitem__(self, item):
        return self.layer_dict[item]

    def max_min_function(self, _func, i):
        func = lambda thalist: _func(thalist, key=lambda p: p[i])[i]

    @property
    def max_x(self):
        max_x = lambda thalist: max(thalist, key=lambda point: point[0])[0] if len(thalist) > 0 else None
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def max_y(self):
        max_y = lambda thalist: max(thalist, key=lambda point: point[1])[1]
        return max(map(lambda layer: max(map(max_y, layer)), self.layer_dict.itervalues()))

    @property
    def min_x(self):
        min_x = lambda thalist: min(thalist, key=lambda point: point[0])[0]
        return min(x for x in map(lambda layer: min(map(min_x, layer)), self.layer_dict.itervalues()) if x is not None)

    @property
    def min_y(self):
        min_y = lambda thalist: min(thalist, key=lambda point: point[1])[1]
        return min(map(lambda layer: min(map(min_y, layer)), self.layer_dict.itervalues()))

    @property
    def width(self):
        return self.max_x -self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    def rotate(self, angle):
        for layer in self.layer_dict.itervalues():
            layer.rotate(angle)

    def move(self, vector):
        for layer in self.layer_dict.itervalues():
            for vectorlist in layer:
                vectorlist.move(vector)

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

    @classmethod
    def create_raster(cls, parts, distance_x=0.1, distance_y=0.1):
        area = cls()
        last_x = 0.
        last_y = 0.
        next_y = []
        for row in parts:
            for part in row:
                part.move([last_x - part.min_x, last_y - part.min_y])
                area.parts.append(part)
                last_x = part.max_x + distance_x
                next_y.append(part.max_y)
            last_y = max(next_y) + distance_y
            last_x = 0.

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
        return min([part.max_y for part in self.parts])