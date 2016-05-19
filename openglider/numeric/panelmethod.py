import PPM
import PPM.vtk_export
import PPM.pan3d
from openglider.numeric.common import GliderCase
from openglider.airfoil import Profile2D

from openglider.glider.in_out import export_3d


class GliderPanelMethod(GliderCase):
    solver = PPM.pan3d.DirichletDoublet0Source0Case3
    wake_length = 1000
    wake_panels = 10

    def __init__(self, glider, v_inf, midribs=0, numpoints=None):
        self.v_inf = v_inf
        self.glider = glider
        self.midribs = midribs
        self.numpoints = numpoints
        self.case = None
        self.panels = None

    def get_panels(self):
        # x_values = Profile2D.cos_distribution(self.numpoints)
        # glider = self.glider.copy()
        # if self.midribs == 0:
        #     glider.apply_mean_ribs()
        # glider.profile_x_values = x_values
        # ribs = glider.return_ribs(self.midribs)
        #
        # num = self.midribs + 1
        # #will hold all the points
        # ribs = []
        # ribs_pos = []
        # for cell_no, cell in enumerate(glider.cells):
        #     for y in range(num):
        #         ribs.append(cell.midrib(y * 1. / num).data)
        #         ribs_pos
        #
        # ribs.append(self.cells[-1].midrib(1.).data)
        return export_3d.PPM_Panels(self.glider, self.midribs, self.numpoints, symmetric=True)

    def run(self):
        self.case = self.solver()
        self.panels = self.panels or self.get_panels()
        self.case.panels = self.panels[1]
        self.case.trailing_edges = self.panels[2]
        self.case.A_ref = self.glider.area
        self.case.vinf = PPM.Vector3(*self.v_inf)
        self.case.create_wake(self.wake_length, self.wake_panels)
        return self.case.run()

    def export_vtk(self, path):
        assert self.panels is not None
        writer = PPM.vtk_export.CaseToVTK(self.case, path)
        writer.write_panels()
        writer.write_wake_panels()

    def get_druckinterpolation(self):
        """
        Mir wolln a interpolation für x = (0, rib_no), y = (-1, 1)
        :return:
        """




