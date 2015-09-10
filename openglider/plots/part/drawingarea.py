import io
import svgwrite
import svgwrite.container
import svgwrite.shapes

from openglider.plots import config
from openglider.utils.css import get_material_color, normalize_class_names

__author__ = 'simon'


class DrawingArea():
    def __init__(self, parts=None):
        self.parts = parts or []

    def __json__(self):
        return {"parts": self.parts}

    @classmethod
    def create_raster(cls, parts, distance_x=0.2, distance_y=0.1):
        """

        :param parts: [[p1_1, p1_2], [p2_1, p2_2],...]
        :param distance_x: grid distance (x)
        :param distance_y: grid distance (y)
        :return: DrawingArea
        """
        parts_flat = []
        for column in parts:
            parts_flat += column
        area = cls(parts_flat)
        area.rasterize(len(parts), distance_x, distance_y)

        return area

    def rasterize(self, columns, distance_x=0.2, distance_y=0.1):
        column_lst = [[] for _ in range(columns)]

        for i, part in enumerate(self.parts):
            column = i%columns
            column_lst[column].append(part)

        distance_y = distance_y or distance_x
        last_x = 0.
        last_y = 0.
        next_x = [0.]
        for col in column_lst:
            for part in col:
                part.move([last_x - part.min_x, last_y - part.min_y])
                #area.parts.append(part)
                last_y = part.max_y + distance_y
                next_x.append(part.max_x)
            last_x = max(next_x) + distance_x
            last_y = 0.


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
        group.scale(1, -1)  # svg coordinate system is x->right y->down

        for part in self.parts:
            part_group = svgwrite.container.Group()

            for layer_name, layer_config in config["layers"].items():
                # todo: simplify
                if layer_name in part.layers:
                    lines = part.layers[layer_name]
                    for line in lines:
                        element = svgwrite.shapes.Polyline(line, **layer_config)
                        classes = [layer_name]
                        if part.material_code:
                            classes.append(part.material_code)
                        element.attribs["class"] = " ".join(classes)
                        part_group.add(element)

            group.add(part_group)

        return group

    def get_svg_drawing(self, unit="mm"):
        width, height = self.width, self.height
        drawing = svgwrite.Drawing(size=[("{}"+unit).format(n) for n in (width, height)])
        drawing.viewbox(self.min_x, -self.max_y, self.width, self.height)
        group = self.get_svg_group()
        drawing.add(group)

        return drawing

    @staticmethod
    def add_svg_styles(drawing):
        style = svgwrite.container.Style()
        styles = {}

        def add_style(elem):
            classes = elem.attribs.get("class", "")
            normalized = normalize_class_names(classes)

            if normalized:
                elem.attribs["class"] = normalize_class_names(classes)

            for _class in classes.split(" "):
                colour = get_material_color(_class)
                _class_new = normalize_class_names(_class)

                if colour:
                    styles[_class_new] = ["fill: {}".format(colour)]
            if hasattr(elem, "elements"):
                for sub_elem in elem.elements:
                    add_style(sub_elem)

        add_style(drawing)

        for cls, attribs in styles.items():
            style.append(".{} {{\n".format(cls))
            for attrib in attribs:
                style.append("\t{};\n".format(attrib))
            style.append("}\n")
        drawing.defs.add(style)

        return drawing

    def _repr_svg_(self):
        width = 600
        height = int(width * self.height/self.width)+1
        drawing = self.get_svg_drawing()
        drawing["width"] = "{}px".format(width)
        drawing["height"] = "{}px".format(height)

        self.add_svg_styles(drawing)


        return drawing.tostring()

    def export_svg(self, path, add_styles=False):
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

    def group_materials(self):
        dct = {}
        for part in self.parts:
            code = part.material_code
            if code not in dct:
                dct[code] = DrawingArea()
            dct[code].parts.append(part)

        return dct
