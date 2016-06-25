import os
import math

import numpy
import svgwrite
import svgwrite.container
import svgwrite.shapes

from openglider.plots import config
from openglider.plots.drawing.part import PlotPart
from openglider.utils.css import get_material_color, normalize_class_names
from openglider.vector import PolyLine2D
from openglider.vector.text import Text


class DrawingArea(object):
    def __init__(self, parts=None):
        self.parts = parts or []

    def __json__(self):
        return {"parts": self.parts}

    def copy(self):
        return self.__class__([p.copy() for p in self.parts])

    def clear(self):
        self.parts.clear()

    @classmethod
    def stack_column(cls, parts, distance, center_x=True):
        column_dwg = cls()
        y = 0
        widths = [part.width for part in parts]
        max_width = max(widths)
        for width, part in zip(widths, parts):
            if isinstance(part, DrawingArea):
                drawing = part
            else:
                drawing = cls([part])

            x = (max_width - width)/2
            drawing.move_to([x,y])

            y += drawing.height
            y += distance

            column_dwg.join(drawing)

        return column_dwg

    @classmethod
    def stack_row(cls, parts, distance, center_y=True):
        row_dwg = cls()
        x = 0
        heights = [part.height for part in parts]
        max_height = max(heights)
        for height, part in zip(heights, parts):
            if isinstance(part, DrawingArea):
                drawing = part
            else:
                drawing = cls([part])

            y = (max_height - height)/2
            drawing.move_to([x,y])

            x += drawing.width
            x += distance

            row_dwg.join(drawing)

        return row_dwg

    @classmethod
    def stack_horizontal(cls, parts, distance_x=0, distance_y=0):
        """

        :param parts:
        :param distance_x:
        :param distance_y:
        :return: DrawingArea
        """
        rows = len(parts)
        if not rows:
            return cls([])
        columns = max(len(row) for row in parts)
        parts_copy = [[p.copy() for p in row] for row in parts]
        all_parts = []

        heights = [0 for _ in range(rows)]
        widths = [0 for _ in range(columns)]

        for row_no, row in enumerate(parts_copy):
            # vertical

            for column_no, part in enumerate(row):
                # horizontal
                part.minimize_area()
                #part.move([-part.min_x, -part.min_y])

                widths[column_no] = max(widths[column_no], part.width)
                heights[row_no] = max(heights[row_no], part.height)

        y = 0
        for row_no, row in enumerate(parts_copy):
            x = 0
            for column_no, part in enumerate(row):
                part.move_to([x, y])

                x += widths[column_no] + distance_x

            y += heights[row_no] + distance_y
            all_parts += row

        return cls(all_parts)

    def draw_border(self, border=0.1, text=None):
        bbox = self.bbox[:]

        bbox[0][0] -= border
        bbox[0][1] -= border
        bbox[1][0] += border
        bbox[1][1] -= border
        bbox[2][0] += border
        bbox[2][1] += border
        bbox[3][0] -= border
        bbox[3][1] += border

        bbox.append(bbox[0])

        data = [PolyLine2D(bbox)]

        if text is not None:
            _text = Text(text, bbox[0], bbox[1], valign=-0.5, size=0.1)
            data += _text.get_vectors()
        border = PlotPart(drawing_boundary=data)
        self.parts.append(border)


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

    def rasterize(self, columns=None, distance_x=0.2, distance_y=0.1):
        """
        create a raster with cells containing the parts
        """
        columns = columns or round(math.sqrt(len(self.parts)))
        columns = int(columns)  # python2 fix
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

    def move_to(self, vector):
        diff = numpy.array(self.bbox[0])-vector
        self.move(-diff)

    def append_top(self, other, distance):
        assert isinstance(other, DrawingArea)

        if self.parts:
            y0 = self.max_y + distance
        else:
            y0 = 0

        other.move_to([0, y0])
        self.parts += other.parts

    def join(self, other):
        assert isinstance(other, DrawingArea)
        self.parts += other.parts

    @classmethod
    def import_dxf(cls, dxfile):
        """
        Imports groups and blocks from a dxf file
        :param dxfile: filename
        :return:
        """
        import ezdxf
        dxf = ezdxf.readfile(dxfile)
        dwg = cls()

        groups = list(dxf.groups)

        for panel_name, panel in groups:
            new_panel = PlotPart(name=panel_name)
            dwg.parts.append(new_panel)

            for entity in panel:
                layer = entity.dxf.layer
                new_panel.layers[layer].append(PolyLine2D([p[:2] for p in entity]))

        #blocks = list(dxf.blocks)
        blockrefs = dxf.modelspace().query("INSERT")

        for blockref in blockrefs:
            name = blockref.dxf.name
            block = dxf.blocks.get(name)

            new_panel = PlotPart(name=block.name)
            dwg.parts.append(new_panel)

            for entity in block:
                layer = entity.dxf.layer
                try:
                    line = [v.dxf.location[:2] for v in entity]
                    if entity.dxf.flags % 2:
                        line.append(line[0])
                    new_panel.layers[layer].append(PolyLine2D(line))
                except:
                    pass


            new_panel.rotate(-blockref.dxf.rotation * math.pi / 180)
            new_panel.move(blockref.dxf.insert[:2])

            # block.name
        #return blocks
        return dwg

    def get_svg_group(self, config=config.sewing_config):
        group = svgwrite.container.Group()
        group.scale(1, -1)  # svg coordinate system is x->right y->down

        for part in self.parts:
            part_group = svgwrite.container.Group()

            for layer_name in part.layers:
                # todo: simplify
                if layer_name in config["layers"]:
                    layer_config = config["layers"][layer_name]
                else:
                    layer_config = {"stroke": "black", "fill": "none", "stroke-width": "1"}

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

    def get_svg_drawing(self, unit="mm", border=0.02):
        border_w, border_h = [2*border*x for x in (self.width, self.height)]
        width, height = self.width+border_w, self.height+border_h

        drawing = svgwrite.Drawing(size=[("{}"+unit).format(n) for n in (width, height)])
        drawing.viewbox(self.min_x-border_w/2, -self.max_y-border_h/2, width, height)
        group = self.get_svg_group()
        drawing.add(group)

        return drawing

    @staticmethod
    def add_svg_styles(drawing):
        style = svgwrite.container.Style()
        styles = {}

        # recursive
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

        for css_class, attribs in styles.items():
            style.append(".{} {{\n".format(css_class))
            for attrib in attribs:
                style.append("\t{};\n".format(attrib))
            style.append("}\n")
        style.append("\nline { vector-effect: non-scaling-width }")
        style.append("\npolyline { vector-effect: non-scaling-width }")
        drawing.defs.add(style)

        return drawing

    def _repr_svg_(self):
        width = 800
        height = int(width * self.height/self.width)+1
        drawing = self.get_svg_drawing()
        self.add_svg_styles(drawing)
        drawing["width"] = "{}px".format(width)
        drawing["height"] = "{}px".format(height)

        #self.add_svg_styles(drawing)

        return drawing.tostring()

    def export_svg(self, path, add_styles=False):
        drawing = self.get_svg_drawing()

        if add_styles:
            self.add_svg_styles(drawing)

        with open(path, "w") as outfile:
            drawing.write(outfile)

    def export_dxf(self, path, dxfversion="AC1015"):
        import ezdxf
        drawing = ezdxf.new(dxfversion=dxfversion)

        drawing.header["$EXTMAX"] = (self.max_x, self.max_y, 0)
        drawing.header["$EXTMIN"] = (self.min_x, self.min_y, 0)
        ms = drawing.modelspace()

        for part in self.parts:
            group = drawing.groups.new()
            with group.edit_data() as part_group:
                for layer_name, layer in part.layers.items():
                    if layer_name not in drawing.layers:
                        attributes = layer._get_dxf_attributes()
                        drawing.layers.new(name=layer_name, dxfattribs=attributes)

                    for elem in layer:
                        dxfattribs = {"layer": layer_name}
                        if len(elem) == 1:
                            dxf_obj = ms.add_point(elem[0], dxfattribs=dxfattribs)
                        else:
                            dxf_obj = ms.add_lwpolyline(elem, dxfattribs=dxfattribs)
                            if len(elem) > 2 and all(elem[-1] == elem[0]):
                                dxf_obj.closed = True
                        part_group.append(dxf_obj)

        drawing.saveas(path)
        return drawing

    ntv_layer_config = {
        "C": ["cuts"],
        "P": ["marks", "text"],
        "R": ["stitches"]
    }

    def export_ntv(self, path):
        filename = os.path.split(path)[-1]

        def format_line(line):
            a = "\nA {} ".format(len(line))
            b = " ".join(["({:.5f},{:.5f})".format(p[0], p[1]) for p in line])
            return a+b

        with open(path, "w") as outfile:
            # head
            outfile.write("A {} {} 1 1 0 0 0 0\n".format(len(filename), filename))
            for part in self.parts:
                # part-header: 1A {name}, {position_x} {pos_y} {rot_degrees} {!derivePerimeter} {useAngle} {flipped}
                part_header = "\n1A {len_name} {name} ({pos_x}, {pos_y}) {rotation_deg} 0 0 0 0 0"
                name = part.name or "unnamed"
                args = {"len_name": len(name),
                        "name": name,
                        "pos_x": 0,
                        "pos_y": 0,
                        "rotation_deg": 0}
                outfile.write(part_header.format(**args))

                # part-boundary
                part_boundary = "\n{boundary_len} {line}"
                #outfile.write()

                for plottype in self.ntv_layer_config:
                    for layer_origin in self.ntv_layer_config[plottype]:
                        for line in part.layers[layer_origin]:
                            # line-header type: (R->ignore, P->plot, C->cut
                            outfile.write("\n1A P 0 {} 0 0 0".format(plottype))
                            outfile.write(format_line(line))


                # part-end
                outfile.write("\n0\n")


            # end
            outfile.write("\n0")

    def scale_a4(self):
        width = max(self.width, self.height)
        height = min(self.width, self.height)
        width_a4, height_a4 = 297, 210

        factor = min(width_a4/width, height_a4/height)
        self.scale(factor)
        return self

    def group_materials(self):
        dct = {}
        for part in self.parts:
            code = part.material_code
            if code not in dct:
                dct[code] = DrawingArea()
            dct[code].parts.append(part)

        return dct

    def scale(self, factor):
        for part in self.parts:
            part.scale(factor)

        return self
