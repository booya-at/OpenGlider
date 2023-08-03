import logging

import euklid
from openglider.glider.cell import DiagonalRib
from openglider.glider.cell.cell import Cell
from openglider.plots.config import PatternConfig
from openglider.plots.usage_stats import Material, MaterialUsage
from openglider.utils.config import Config
from openglider.vector.drawing import PlotPart
from openglider.vector.text import Text


logger = logging.getLogger(__name__)


class DribPlot:
    DefaultConf = PatternConfig

    def __init__(self, drib: DiagonalRib, cell: Cell, config: Config):
        # We are unwrapping the right side of the wing (flying direction).
        # rib1 -> left side / inside
        # rib2 -> right side / outside
        # seen from the bottom => mirror
        self.drib = drib
        self.cell = cell
        self.config = self.DefaultConf(config)

        left, right = self.drib.get_flattened(self.cell)
        p1, p2 = left.nodes[0], right.nodes[0]
        left = left.mirror(p1, p2)
        right = right.mirror(p1, p2)

        center_left = left.get(left.walk(0, left.get_length()/2))
        center_right = right.get(right.walk(0, right.get_length()/2))
        angle = (center_right - center_left).angle()

        self.left = left.rotate(-angle, euklid.vector.Vector2D([0,0]))
        self.right = right.rotate(-angle, euklid.vector.Vector2D([0,0]))

        # left and right are going top to bottom -> offset reversed
        self.left_out = self.left.offset(self.config.allowance_general)
        self.right_out = self.right.offset(-self.config.allowance_general)

    def get_left(self, x: float) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        return self.get_p1_p2(x, right_side=False)

    def get_right(self, x: float) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        return self.get_p1_p2(x, right_side=True)

    def validate(self, x: float, right_side: bool=False) -> bool:
        if not right_side:
            side_obj = self.drib.left
            rib = self.cell.rib1
        else:
            side_obj = self.drib.right
            rib = self.cell.rib2

        if not side_obj.is_lower and not side_obj.is_upper:
            raise ValueError(f"invalid height: {side_obj.height}")

        boundary = [side_obj.start_x(rib), side_obj.end_x(rib)]
        boundary.sort()

        if not boundary[0] <= x <= boundary[1]:
            raise ValueError(f"not in boundaries: {x} ({boundary[0]} / {boundary[1]}")

        return True

    def get_p1_p2(self, x: float, right_side: bool=False) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        self.validate(x, right_side=right_side)

        if not right_side:
            side_obj = self.drib.left
            rib = self.cell.rib1
            inner = self.left
            outer = self.left_out
        else:
            side_obj = self.drib.right
            rib = self.cell.rib2
            inner = self.right
            outer = self.right_out
        
        if side_obj.start_x(rib) > x or side_obj.end_x(rib) < x:
            raise ValueError(f"invalid x: {x} ({side_obj.start_x} / {side_obj.end_x}")

        foil = rib.profile_2d
        # -1 -> lower, 1 -> upper
        foil_side = 1 if side_obj.is_lower else -1

        x1 = side_obj.start_x(rib) * foil_side
        x2 = x * foil_side

        ik_1 = foil(x1)
        ik_2 = foil(x2)
        length = foil.curve.get(ik_1, ik_2).get_length() * rib.chord

        ik_new = inner.walk(0, length)
        return inner.get(ik_new), outer.get(ik_new)
    
    def _insert_center_marks(self, plotpart: PlotPart) -> None:
        def insert_center_mark(inner: euklid.vector.PolyLine2D, outer: euklid.vector.PolyLine2D) -> None:
            ik = inner.walk(0, inner.get_length()/2)
            p1 = inner.get(ik)
            p2 = outer.get(ik)

            for layer_name, marks in self.config.marks_diagonal_center(p1, p2).items():
                plotpart.layers[layer_name] += marks

        # put center marks only on lower sides of diagonal ribs, always on straight ones
        if self.drib.left.is_lower or self.drib.is_upper:
            insert_center_mark(self.left, self.left_out)

        if self.drib.right.is_lower or self.drib.is_upper:
            insert_center_mark(self.right, self.right_out)
    
    def _insert_controlpoints(self, plotpart: PlotPart) -> None:
        x: float
        sides = (
            (False, self.cell.rib1),
            (True, self.cell.rib2)
        )

        for side, rib in sides:
            for x in self.config.get_controlpoints(rib):
                try:
                    p1, p2 = self.get_p1_p2(x, side)
                    for layer_name, marks in self.config.marks_controlpoint(p1, p2).items():
                        plotpart.layers[layer_name] += marks
                except ValueError:
                    continue

    def _insert_attachment_points(self, plotpart: PlotPart) -> None:
        def _add_mark(name: str, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> None:
            for layer_name, marks in self.config.marks_attachment_point(p1, p2).items():
                plotpart.layers[layer_name] += marks
            plotpart.layers["marks"] += Text(name, p1 + (p1 - p2), p1).get_vectors()

        for attachment_point in self.cell.rib1.attachment_points:
            try:
                p1, p2 = self.get_left(attachment_point.rib_pos.si)
            except ValueError:
                continue
            _add_mark(attachment_point.name, p1, p2)

        for attachment_point in self.cell.rib2.attachment_points:
            try:
                p1, p2 = self.get_right(attachment_point.rib_pos.si)
            except ValueError:
                continue
            _add_mark(attachment_point.name, p1, p2)

    def _insert_text(self, plotpart: PlotPart, reverse: bool=False) -> None:
        if reverse:
            node_index = -1
        else:
            node_index = 0
        # text_p1 = left_out[0] + self.config.drib_text_position * (right_out[0] - left_out[0])
        plotpart.layers["text"] += Text(f" {self.drib.name} ",
                                        self.left.nodes[node_index],
                                        self.right.nodes[node_index],
                                        size=self.config.drib_allowance_folds * 0.6,
                                        height=0.6,
                                        valign=0.6).get_vectors()

    def flatten(self) -> PlotPart:
        return self._flatten(self.drib.num_folds)

    def _flatten(self, num_folds: int) -> PlotPart:
        plotpart = PlotPart(material_code=self.drib.material_code, name=self.drib.name)

        if num_folds > 0:
            print("a", num_folds, self.drib.num_folds)
            alw2 = self.config.drib_allowance_folds
            cut_front = self.config.cut_diagonal_fold(amount=alw2, num_folds=num_folds)
            cut_back = self.config.cut_diagonal_fold(amount=-alw2, num_folds=num_folds)
            
            cut_front_result = cut_front.apply([(self.left, 0), (self.right, 0)], self.left_out, self.right_out)
            cut_back_result = cut_back.apply([(self.left, len(self.left) - 1), (self.right, len(self.right) - 1)], self.left_out, self.right_out)
            
            plotpart.layers["cuts"] += [self.left_out.get(cut_front_result.index_left, cut_back_result.index_left) +
                                        cut_back_result.curve +
                                        self.right_out.get(cut_back_result.index_right, cut_front_result.index_right) +
                                        cut_front_result.curve.reverse()
            ]

        else:
            print("b", num_folds, self.drib.num_folds)
            #p1 = self.left_out.cut(self.left.get(0), self.right.get(0), 0)[0]
            #p2 = self.left_out.cut(self.left.get(len(self.left)-1), self.right.get(len(self.right)-1), len(self.left_out))[0]
            #p3 = self.right_out.cut(self.left.get(0), self.right.get(0), 0)[0]
            #p4 = self.right_out.cut(self.left.get(len(self.left)-1), self.right.get(len(self.right)-1), len(self.right_out))[0]

            #outer = self.left_out.get(p1, p2)
            #outer += self.right_out.get(p3,p4).reverse()
            #outer += euklid.vector.PolyLine2D([self.left_out.get(p1)])

            outer = self.left_out.copy()
            outer += euklid.vector.PolyLine2D([self.left.nodes[-1]])
            outer += euklid.vector.PolyLine2D([self.right.nodes[-1]])
            outer += self.right_out.reverse()
            outer += euklid.vector.PolyLine2D([self.right.nodes[0]])
            outer += euklid.vector.PolyLine2D([self.left.nodes[0]])
            outer += euklid.vector.PolyLine2D([self.left_out.nodes[0]])
            #outer += euklid.vector.PolyLine2D([self.left_out.get(p1)])
            plotpart.layers["cuts"].append(outer)

        for curve in self.drib.get_holes(self.cell)[0]:
            plotpart.layers["cuts"].append(curve)

        plotpart.layers["marks"].append(euklid.vector.PolyLine2D([self.left.get(0), self.right.get(0)]))
        plotpart.layers["marks"].append(euklid.vector.PolyLine2D([self.left.get(len(self.left) - 1), self.right.get(len(self.right) - 1)]))

        plotpart.layers["stitches"] += [self.left, self.right]

        self._insert_attachment_points(plotpart)
        self._insert_center_marks(plotpart)
        self._insert_controlpoints(plotpart)

        # mirror -> watch from above
        #p1 = euklid.vector.Vector2D([0, 0])
        #p2 = euklid.vector.Vector2D([1, 0])
        #plotpart = plotpart.mirror(p1, p2)
        self._insert_text(plotpart)
        
        self.plotpart = plotpart
        return plotpart
    
    def get_material_usage(self) -> MaterialUsage:
        dwg = self.plotpart

        curves = dwg.layers["envelope"].polylines
        usage = MaterialUsage()
        material = Material(weight=38, name="dribs")

        if curves:
            area = curves[0].get_area()
        
            for curve in self.drib.get_holes(self.cell)[0]:
                area -= curve.get_area()
                
            usage.consume(material, area)

        return usage


class StrapPlot(DribPlot):
    def flatten(self) -> PlotPart:
        return self._flatten(self.drib.num_folds)
