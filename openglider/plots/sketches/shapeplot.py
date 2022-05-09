import logging
import math
from typing import Iterator, List, Optional

import euklid
import numpy as np
import openglider.plots.marks as marks
from attr import attr
from openglider.glider import GliderProject
from openglider.glider.cell.panel import Panel, PanelCut
from openglider.utils.dataclass import dataclass
from openglider.vector.drawing import Layout, PlotPart
from openglider.vector.text import Text

logger = logging.getLogger(__name__)


@dataclass
class ShapePlotConfig:
    design_lower: bool = False
    design_upper: bool = False
    baseline: bool = False
    grid: bool = False
    attachment_points: bool = False
    lines: bool = False
    cells: bool = True
    cell_names: bool = False
    rib_names: bool = False
    straps: bool = False
    diagonals: bool = False

    scale_area: Optional[float] = None
    scale_span: Optional[float] = None

    def view_layers(self):
        layers = {}
        for attribute in self.__annotations__:
            if not attribute.startswith("scale"):
                layers[attribute] = getattr(self, attribute)
            
        return layers
    
    def copy(self):
        new = ShapePlotConfig()
        for attribute in self.__annotations__:
            setattr(new, attribute, getattr(self, attribute))

        return new 


class ShapePlot(object):
    project: GliderProject
    config: ShapePlotConfig
    attachment_point_mark = marks.Cross(name="attachment_point", rotation=np.pi/4)

    def __init__(self, project: GliderProject, drawing=None):
        super(ShapePlot, self).__init__()
        self.project = project
        self.glider_2d = project.glider
        self.glider_3d = project.glider_3d
        self.drawing = drawing or Layout()

        self.reference_area = self.glider_2d.shape.area
        self.reference_span = self.glider_2d.shape.span

        self.shape_r = self.glider_2d.shape.get_half_shape()

        self.shape_l = self.shape_r.copy().scale(x=-1)
        self.shapes = [self.shape_r, self.shape_l]

        self.config = None
    
    def redraw(self, config: ShapePlotConfig, force=False):
        if force:
            self.shape_r = self.glider_2d.shape.get_half_shape()

            self.shape_l = self.shape_r.copy().scale(x=-1)
            self.shapes = [self.shape_r, self.shape_l]
        if config != self.config or force:
            logger.info("needs redraw")
            self.drawing = Layout()

            for layer_name, show_layer in config.view_layers().items():
                if show_layer:
                    f = getattr(self, f"draw_{layer_name}")
                    f(left=True)
                    f(left=False)
        
            if config.scale_area:
                self.drawing.scale(math.sqrt(config.scale_area/self.reference_area))
            elif config.scale_span:
                self.drawing.scale(config.scale_span/self.reference_span)
            
            self.config = config
        
        return self.drawing

    def copy(self):
        drawing = self.drawing.copy()

        return ShapePlot(self.project, drawing)

    def _rib_range(self, left):
        start = 0
        end = self.project.glider.shape.half_cell_num
        if self.glider_2d.shape.has_center_cell and left:
            start = 1

        return range(start, end+1)

    
    def _cell_range(self, left):
        start = 0
        end = self.project.glider.shape.half_cell_num
        if self.glider_2d.shape.has_center_cell and left:
            start = 1

        return range(start, end)
    
    def draw_design_lower(self, left=False):
        return self.draw_design(True, left)
    
    def draw_design_upper(self, left=False):
        return self.draw_design(False, left)

    def draw_design(self, lower=True, left=False) -> "ShapePlot":
        shape = self.shapes[left]

        panels = self.glider_2d.get_panels()

        for cell_no in self._cell_range(left):
            cell_panels = panels[cell_no]

            def match(panel):
                if lower:
                    # -> either on the left or on the right it should go further than 0
                    return panel.cut_back.x_left > 0 or panel.cut_back.x_right > 0
                else:
                    # should start before zero at least once
                    return panel.cut_front.x_left < 0 or panel.cut_front.x_right < 0

            cell_side_panels: Iterator[Panel] = filter(match, cell_panels)

            for panel in cell_side_panels:
                def normalize_x(val):
                    if lower:
                        return max(val, 0)
                    else:
                        return max(-val, 0)

                def get_cut_line(cut: PanelCut):
                    left = shape.get_point(cell_no, normalize_x(cut.x_left))
                    right = shape.get_point(cell_no+1, normalize_x(cut.x_right))

                    if cut.x_center is not None:
                        center = shape.get_point(cell_no+0.5, normalize_x(cut.x_center))
                        return euklid.spline.BSplineCurve([left, center, right]).get_sequence(8)
                    
                    return euklid.vector.PolyLine2D([left, right])
                
                l1 = get_cut_line(panel.cut_front)
                l2 = get_cut_line(panel.cut_back).reverse()

                self.drawing.parts.append(PlotPart(
                    cuts=[euklid.vector.PolyLine2D(l1.nodes + l2.nodes + [l1.nodes[0]])],
                    material_code=f"{panel.material}#{panel.material.color_code}"
                ))

        return self

    def draw_baseline(self, pct=None, left=False):
        shape = self.shapes[left]

        if pct is None:
            pct = self.glider_2d.shape.baseline_pos

        part = PlotPart()
        
        line = euklid.vector.PolyLine2D([shape.get_point(rib, pct) for rib in self._rib_range(left)])
        part.layers["marks"].append(line)
        self.drawing.parts.append(part)

    def draw_grid(self, num=11, left=False):
        import numpy as np
        part = PlotPart()

        for x in np.linspace(0, 1, num):
            self.draw_baseline(x, left=left)

        self.draw_cells(left=left)
        return self

    def draw_attachment_points(self, add_text=True, left=False):
        shape = self.shapes[left]

        part = PlotPart()
        for attachment_point in self.glider_2d.lineset.get_upper_nodes():
            rib_no = attachment_point.cell_pos + attachment_point.cell_no

            # glider2d does not contain the mirrored rib:
            p1 = shape.get_point(rib_no, attachment_point.rib_pos)
            p2 = p1 + [0.2, 0]


            diff = (p2-p1)*0.2
            cross_left = p1 - diff
            cross_right = p1 + diff

            cross = self.attachment_point_mark(cross_left, cross_right)
            part.layers["marks"] += cross

            if add_text and attachment_point.name:
                p1 = p1 + [0, 0.02]
                p2 = p2 + [0, 0.02]
                text = Text(" {} ".format(attachment_point.name), p1, p2)
                vectors = text.get_vectors()
                part.layers["text"] += vectors

        self.drawing.parts.append(part)

    def draw_cells(self, left=False):
        shape = self.shapes[left]

        cells = []

        for cell_no in self._cell_range(left):
            p1 = shape.get_point(cell_no, 0)
            p2 = shape.get_point(cell_no+1, 0)
            p3 = shape.get_point(cell_no+1, 1)
            p4 = shape.get_point(cell_no, 1)
            cells.append(euklid.vector.PolyLine2D([p1,p2,p3,p4,p1]))

        self.drawing.parts.append(PlotPart(
            marks=cells,
            material_code="cell_numbers")
        )

    def draw_cell_names(self, left=False):
        shape = self.shapes[left]
        names = []
        
        for cell_no in self._cell_range(left):
            cell = self.glider_3d.cells[cell_no]
            p1 = shape.get_point(cell_no+0.5, 0)
            p2 = shape.get_point(cell_no+0.5, 1)
            width = shape.get_point(cell_no+1, 0)[0] - p1[0]

            text = Text(cell.name, p1, p2, size=width*0.8, valign=0, align="center")
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            text=names,
            material_code="cell_numbers")
        )

    def draw_rib_names(self, left=False):
        shape = self.shapes[left]
        midrib = self.glider_2d.shape.has_center_cell
        names = []

        for rib_no in self._rib_range(left):
            rib = self.glider_3d.ribs[rib_no]
            rib_no = max(0, rib_no)
            p1 = shape.get_point(rib_no, -0.05)
            try:
                p2 = shape.get_point(rib_no + 1, 0)
            except IndexError:
                p2 = shape.get_point(rib_no - 1, 0)
            diff = abs(p1[0]- p2[0]) # cell distance
            p2[0] = p1[0]
            p2[1] = p1[1] + diff

            # notwendig?
            # if rib_no == 0 and midrib:
            #     p1[0] = -p1[0]
            #     p2[0] = -p2[0]
            #     continue

            text = Text(rib.name, p1, p2, valign=0)
            names += text.get_vectors()

        self.drawing.parts.append(PlotPart(
            text=names,
            material_code="rib_numbers")
        )

    def draw_straps(self, left=False):
        shape = self.shapes[left]

        for cell_no in self._cell_range(left):
            cell = self.glider_3d.cells[cell_no]
            for diagonal in cell.straps:
                left = [abs(x) for x in (diagonal.left.start_x, diagonal.left.end_x)]
                right = [abs(x) for x in (diagonal.right.start_x, diagonal.right.end_x)]

                points_left = [shape.get_point(cell_no, p) for p in left]
                points_right = [shape.get_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[euklid.vector.PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

        return self

    def draw_diagonals(self, left=False):
        shape = self.shapes[left]

        for cell_no in self._cell_range(left):
            cell = self.glider_3d.cells[cell_no]
            for diagonal in cell.diagonals:
                left = [abs(x) for x in (diagonal.left.start_x, diagonal.left.end_x)]
                right = [abs(x) for x in (diagonal.right.start_x, diagonal.right.end_x)]

                points_left = [shape.get_point(cell_no, p) for p in left]
                points_right = [shape.get_point(cell_no+1, p) for p in right]

                self.drawing.parts.append(PlotPart(marks=[euklid.vector.PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

        return self

    def draw_lines(self, left=False):
        #self.draw_design(lower=True)
        #self.draw_design(lower=True, left=True)
        #self.draw_attachment_points(True)
        #self.draw_attachment_points(True, left=True)

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
                layer = pp.layers[f"line_{i}"]
                line = euklid.vector.PolyLine2D([
                        line.lower_node.get_2D(self.glider_2d.shape),
                        line.upper_node.get_2D(self.glider_2d.shape)
                    ])
                if left:
                    line = line.scale([-1, 1])

                layer += [line]
                self.drawing.parts.append(pp)

        return self


    def export_a4(self, path, fill=False):
        new = self.drawing.copy()
        new.scale_a4()
        
        new.export_pdf(path, fill=fill)

    def _repr_svg_(self):
        new = self.drawing.copy()
        new.scale_a4()
        return new._repr_svg_()
