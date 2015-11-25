import copy
import math
import numpy
from openglider.airfoil import Profile3D
from openglider.utils.cache import CachedObject, cached_property
from openglider.vector import normalize, norm


class BasicCell(CachedObject):
    """
    A very simple cell without any extras like midribs, diagonals,..
    """
    def __init__(self, prof1=None, prof2=None, ballooning=None, name="unnamed_cell"):
        self.prof1 = prof1 or Profile3D([])
        self.prof2 = prof2 or Profile3D([])

        if ballooning is not None:
            self.ballooning_phi = ballooning  # ballooning arcs -> property in cell
        self.name = name

    def point_basic_cell(self, y=0, ik=0):
        ##round ballooning
        return self.midrib(y).point(ik)

    def midrib(self, y_value, ballooning=True, arc_argument=True):
        if y_value == 0:              # left side
            return self.prof1
        elif y_value == 1:            # right side
            return self.prof2
        else:                   # somewhere else
            #self._checkxvals()
            midrib = []

            # Ballooning is considered to be arcs, following 2 (two!) simple rules:
            # 1: x1 = x*d
            # 2: x2 = R*normvekt*(cos(phi2)-cos(phi)
            # 3: norm(d)/r*(1-x) = 2*sin(phi(2))

            for i, _ in enumerate(self.prof1.data):  # Arc -> phi(bal) -> r  # oder so...
                diff = self.prof1[i] - self.prof2[i]
                if ballooning and self.ballooning_radius[i] > 0.:
                    if arc_argument:
                        d = 0.5 + math.sin(self.ballooning_phi[i] * (y_value - 0.5)) / math.sin(self.ballooning_phi[i])
                        h = math.cos(self.ballooning_phi[i] * (1 - 2 * y_value)) - self.ballooning_cos_phi[i]
                    else:
                        d = y_value
                        h = math.cos(math.asin((2 * d - 1)*math.sin(self.ballooning_phi[i]))) -  math.cos(self.ballooning_phi[i])
                else:  # Without ballooning
                    d = y_value
                    h = 0.
                midrib.append(self.prof1[i] - diff * d +
                              self.normvectors[i] * h * self.ballooning_radius[i])

            return Profile3D(midrib)

    @cached_property('prof1', 'prof2')
    def normvectors(self, j=None):
        prof1 = self.prof1.data
        prof2 = self.prof2.data
        p1 = self.prof1.tangents
        p2 = self.prof2.tangents
        # cross differenzvektor, tangentialvektor
        return [normalize(numpy.cross(p1[i] + p2[i], prof1[i] - prof2[i])) for i in range(len(prof1))]

    @cached_property('ballooning_phi')
    def ballooning_cos_phi(self):
        tolerance = 0.00001
        return [numpy.cos(phi) if phi > tolerance else 0 for phi in self.ballooning_phi]

    @cached_property('ballooning_phi', 'prof1', 'prof2')
    def ballooning_radius(self):
        tolerance = 0.00001
        return [norm(p1-p2)/(2*numpy.sin(phi)) if phi>tolerance else 0
                for p1, p2, phi in zip(self.prof1, self.prof2, self.ballooning_phi)]
        # radius = []
        # for i, phi in enumerate(self.ballooning_phi):
        #     if round(phi, 5) > 0:
        #         radius.append(norm(self.prof1.data[i] - self.prof2.data[i]) / (2*numpy.sin(phi)))
        #     else:
        #         radius.append(0)
        # return radius

    def copy(self):
        return copy.deepcopy(self)