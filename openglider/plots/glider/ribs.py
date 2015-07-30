# coding=utf-8
import collections

from openglider.airfoil import get_x_value
from openglider.plots import sewing_config, PlotPart
from openglider.vector import PolyLine2D
from openglider.vector.text import get_text_vector


class RibPlot:
    def __init__(self, rib, config):
        self.rib = rib
        self.inner = rib.profile_2d.copy().scale(rib.chord)
        self.outer = self.inner.copy().add_stuff(config["allowance"]["general"])
        self.x_values = rib.profile_2d.x_values
        self.config = config
        self.plotpart = PlotPart(name=rib.name, material_code=rib.material_code)

        # insert cut
        self.cut_outer_rib()
        self.plotpart.marks.append(self.inner)

    def insert_mark(self, position, _type):
        mark = self.config["marks"][_type]
        ik = get_x_value(self.x_values, position)
        inner = self.inner[ik]
        outer = self.outer[ik]

        self.plotpart.marks += mark(inner, outer)

    def get_point(self, x, y=-1):
        assert x >= 0
        p = self.rib.profile_2d.profilepoint(x,y)
        return p*self.rib.chord

    def insert_drib_mark(self, drib, right=False):

        if right:
            p1 = drib.right_front
            p2 = drib.right_back
        else:
            p1 = drib.left_front
            p2 = drib.left_back

        if p1[1] == p2[1] == -1:
            self.insert_mark(p1[0], "diagonal")
            self.insert_mark(p2[0], "diagonal")
        elif p1[1] == p2[1] == 1:
            self.insert_mark(-p1[0], "diagonal")
            self.insert_mark(-p2[0], "diagonal")
        else:
            p1 = self.get_point(*p1)
            p2 = self.get_point(*p2)
            self.plotpart.marks.append(PolyLine2D([p1, p2]))

    def cut_outer_rib(self):
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer
        inner_rib = self.inner
        t_e_allowance = self.config["allowance"]["trailing_edge"]
        p1 = inner_rib[0] + [0, 1]
        p2 = inner_rib[0] + [0, -1]
        cuts = outer_rib.new_cut(p1, p2)

        start = next(cuts)
        stop = next(cuts)
        buerzl = PolyLine2D([outer_rib[stop],
                            outer_rib[stop] + [t_e_allowance, 0],
                            outer_rib[start] + [t_e_allowance, 0],
                            outer_rib[start]])
        self.plotpart.cuts += [PolyLine2D(outer_rib[start:stop].data) + buerzl]

    def add_text(self, text):
        self.plotpart.text += get_text_vector(text,
                                              self.get_point(0.03, 0),
                                              self.get_point(0.13, 0))


def get_ribs(glider):
    ribs = collections.OrderedDict()

    for rib_no, rib in enumerate(glider.ribs[glider.has_center_cell:-1]):
        rib_plot = RibPlot(rib, config=sewing_config)
        rib_no += glider.has_center_cell

        # marks for attachment-points
        attachment_points = filter(lambda p: p.rib == rib,
                                   glider.attachment_points)
        for point in attachment_points:
            rib_plot.insert_mark(point.rib_pos, "attachment-point")

        # marks for panel-cuts
        rib_cuts = set()
        left_cell = glider.cells[rib_no - (rib_no > 0)]
        right_cell = glider.cells[rib_no]
        for panel in left_cell.panels:
            rib_cuts.add(panel.cut_front["right"])  # left cell
            rib_cuts.add(panel.cut_back["right"])
        for panel in right_cell.panels:
            rib_cuts.add(panel.cut_front["left"])
            rib_cuts.add(panel.cut_back["left"])
        rib_cuts.remove(1)
        rib_cuts.remove(-1)
        for cut in rib_cuts:
            rib_plot.insert_mark(cut, "panel-cut")

        # holes
        for hole in rib.holes:
            rib_plot.plotpart.cuts.append(hole.get_flattened(rib))

        # Diagonals
        for cell in glider.cells:
            if rib in cell.ribs:
                right = False
                if rib is cell.rib2:
                    right = True
                for diagonal in cell.diagonals:
                    rib_plot.insert_drib_mark(diagonal, right)

        for cell in glider.cells:
            for strap in cell.straps:
                if rib is cell.rib1:  # left
                    rib_plot.insert_mark(strap.left, "strap")
                elif rib is cell.rib2:  # right
                    rib_plot.insert_mark(strap.right, "strap")


        # rigidfoils
        for rigid in rib.rigidfoils:
            rib_plot.plotpart.marks.append(rigid.get_flattened(rib))

        # TEXT
        # TODO: improve (move away from holes?)
        rib_plot.add_text("rib{}".format(rib_no))

        ribs[rib] = rib_plot.plotpart

    return ribs
