from __future__ import annotations
from typing import List, Optional
import copy

import euklid
import numpy as np

VectorList = List[euklid.vector.PolyLine2D]

class Layer(object):
    stroke = "black"
    stroke_width = 1
    visible = True

    def __init__(self, polylines: Optional[VectorList]=None, stroke: str=None, stroke_width: float=1., visible: bool=True):
        self.polylines = polylines or []
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.visible = visible

    def __add__(self, other: Layer | List[euklid.vector.PolyLine2D]):
        self.polylines += other
        return self

    def __iter__(self):
        return iter(self.polylines)

    def __len__(self):
        return len(self.polylines)

    def __json__(self):
        return {
            "polylines": self.polylines,
            "stroke": self.stroke,
            "stroke_width": self.stroke_width
        }

    def append(self, x):
        self.polylines.append(x)

    def copy(self):
        return Layer([p.copy() for p in self])

    def _get_dxf_attributes(self):
        # color mapping: red->1, green->3, blue->5, black->7
        if self.stroke == "red":
            color = 1
        elif self.stroke == "green":
            color = 3
        elif self.stroke == "blue":
            color = 5
        else:
            color = 7

        return {
            "color": color,
        }


class Layers(object):
    def __init__(self, **layers):
        self.layers = layers

    def __repr__(self):
        """pretty-print"""
        lines = ["Layers:"] + ["{} ({})".format(layer_name, len(layer)) for layer_name, layer in self.layers.items()]
        return "\n  - ".join(lines)

    def __getitem__(self, item) -> Layer:
        item = str(item)
        if item in ("name", "material_code"):
            raise KeyError()
        if item not in self.layers:
            self.layers[item] = Layer()
        return self.layers[item]

    def __setitem__(self, key, value):
        if isinstance(value, list):
            self.layers[key] = Layer(value)
        elif isinstance(value, Layer):
            self.layers[key] = value
        else:
            raise ValueError()

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

    def add(self, name, **kwargs):
        layer = Layer(**kwargs)

        self.layers[name] = layer
        return layer
    
    def pop(self, name):
        return self.layers.pop(name)


class PlotPart(object):
    def __init__(self, cuts=None, marks=None, text=None, stitches=None, name=None, material_code="", **layers):
        self.layers = Layers()
        self.layers.add("cuts", stroke="red")
        self.layers.add("marks", stroke="green")
        self.layers.add("stitches", stroke="green")
        self.layers.add("text", stroke="blue")
        self.layers.add("envelope", stroke="white", visible=False)

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
    
    def __iadd__(self, other: "PlotPart"):
        for layer_name, layer in other.layers.items():
            self.layers[layer_name] += layer
        
        return self

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self, p1, p2):
        layers = {}

        for layer_name, layer in self.layers.items():
            layer_new = [line.mirror(p1, p2) for line in layer]
            layers[layer_name] = layer_new

        return PlotPart(**layers, material_code=self.material_code, name=self.name)


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
        value = float("-Inf")

        for layer_name, layer in self.layers.items():
            try:
                value = max(self.max_function(0, layer), value)
            except Exception as e:
                #print("error", layer_name)
                raise Exception(f"error {layer_name}, {len(layer)}, {list(layer)}")
        
        return value


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

    def rotate(self, angle, radians=True):
        if not radians:
            angle = angle * np.pi / 180
        for layer in self.layers.values():
            layer.polylines = [
                polyline.rotate(angle, [0, 0]) for polyline in layer
            ]

    def move(self, vector):
        diff = list(vector)
        for layer_name, layer in self.layers.items():
            layer.polylines = [
                line.move(diff) for line in layer.polylines
            ]

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
            new_part.rotate(np.pi/180)
            if new_part.area < area:
                rotation = alpha
                area = new_part.area
                width = new_part.width
                height = new_part.height

        if width < height:
            rotation -= 90

        self.rotate(rotation*np.pi/180)
        return self

    def scale(self, factor):
        for layer_name, layer in self.layers.items():
            layer.polylines = [
                line.scale(factor) for line in layer.polylines
            ]

    def get_svg_group(self, non_scaling_stroke=True):
        import svgwrite
        import svgwrite.shapes
        import svgwrite.container
        import svgwrite.path

        # if it has an envelope use the envelope to group elements
        if False and "envelope" in self.layers and len(self.layers["envelope"]) == 1:
            envelope = self.layers["envelope"]
            path = self.layers["envelope"][0]
            d = "M {} {}".format(*path[0])
            for p in path[1:]:
                d += " L {} {}".format(*p)
            container = svgwrite.path.Path(d)
            container.attribs["stroke"] = envelope.stroke or "red"
            container.attribs["stroke-width"] = str(envelope.stroke_width)
            container.attribs["fill"] = "none"
            if non_scaling_stroke:
                container.attribs["stroke-width"] += "px"
                container.attribs["style"] = "vector-effect: non-scaling-stroke"
        else:
            container = svgwrite.container.Group()

        container.attribs["id"] = self.name
        container.attribs["class"] = self.material_code

        for layer_name, layer in self.layers.items():
            layer_container = svgwrite.container.Group()
            layer_container.attribs["class"] = layer_name

            for path in layer:
                pl = svgwrite.shapes.Polyline(path)
                pl.attribs["stroke"] = layer.stroke or "black"
                pl.attribs["stroke-width"] = str(layer.stroke_width)
                pl.attribs["fill"] = "none"
                if non_scaling_stroke:
                    pl.attribs["stroke-width"] += "px"
                    pl.attribs["style"] = "vector-effect: non-scaling-stroke"

                layer_container.add(pl)

            container.add(layer_container)

        return container

    def _repr_svg_(self):
        from openglider.vector.drawing import Layout

        return Layout([self])._repr_svg_()