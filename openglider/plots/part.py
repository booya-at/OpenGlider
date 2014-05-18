from openglider.vector import Vectorlist2D


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
            if not isinstance(layer, Vectorlist2D):
                layer = Vectorlist2D(layer)
        self._layer_dict = layer_dict

    def __getitem__(self, item):
        return self.layer_dict[item]

    @property
    def max_x(self):
        max_x = lambda thalist: max(thalist, key=lambda point: point[0])[0]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def max_y(self):
        max_x = lambda thalist: max(thalist, key=lambda point: point[1])[1]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def min_x(self):
        max_x = lambda thalist: min(thalist, key=lambda point: point[0])[0]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def min_y(self):
        max_x = lambda thalist: min(thalist, key=lambda point: point[1])[1]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    def rotate(self, angle):
        for layer in self.layer_dict.itervalues():
            layer.rotate(angle)

    def shift(self, vector):
        for layer in self.layer_dict.itervalues():
            for vectorlist in layer:
                vectorlist.shift(vector)

    def return_layer_svg(self, layer):
        """
        Return a layer scaled for svg_coordinate_system [x,y = (mm, -mm)]
        """
        if layer in self.layer_dict:
            new = []
            for line in self.layer_dict[layer]:
                new.append(map(lambda point: point * [1000, -1000], line))
            return new
        else:
            return None