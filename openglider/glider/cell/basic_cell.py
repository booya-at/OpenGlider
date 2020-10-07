from __future__ import division
import copy
import math
import numpy as np
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

    def midrib(self, y_value, ballooning=True, arc_argument=True, with_numpy=True, close_trailing_edge=False):
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
            if with_numpy:
                l_phi = np.array(self.ballooning_phi)
                l_n = np.array(self.normvectors)
                l_r = np.array(self.ballooning_radius)
                l_diff = self.prof1.data - self.prof2.data

                l_phi = l_phi  + (1e-10 - l_phi) * (l_phi <= 0.)
                l_psi = l_phi * 2 * y_value
                l_h = np.cos(l_phi - l_psi) - np.cos(l_phi)
                l_d = 0.5 * (1 - np.sin(l_phi - l_psi) / np.sin(l_phi))
                l_r = l_r * (l_r > 0.)
                l_midrib = self.prof1.data.T - l_d * l_diff.T + (l_h * l_r) * l_n.T
                return Profile3D(l_midrib.T)

            for i, _ in enumerate(self.prof1.data):  # Arc -> phi(bal) -> r  # oder so...
                diff = self.prof1[i] - self.prof2[i]
                if close_trailing_edge and i in (0, len(self.prof1.data)-1):
                    d = y_value
                    h = 0.
                elif ballooning and self.ballooning_radius[i] > 0.:
                    phi = self.ballooning_phi[i]    # phi is half only the half
                    if arc_argument:
                        psi = phi * 2 * y_value         # psi [-phi:phi]
                        d = 0.5 - 0.5 * math.sin(phi - psi) / math.sin(phi)
                        h = math.cos(phi - psi) - math.cos(phi)
                    else:
                        d = y_value
                        h = math.cos(math.asin((2 * d - 1) * math.sin(phi))) -  math.cos(phi)
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
        p1 = np.array(self.prof1.tangents)
        p2 = np.array(self.prof2.tangents)
        # cross differenzvektor, tangentialvektor
        normal_vec = np.cross(p1 + p2, prof1 - prof2, axis=1).T
        normal_vec /= np.linalg.norm(normal_vec, axis=0)
        return normal_vec.T

    @cached_property('ballooning_phi')
    def ballooning_cos_phi(self):
        tolerance = 0.00001
        phi = np.array(self.ballooning_phi)
        return np.cos(phi)

    @cached_property('ballooning_phi', 'prof1', 'prof2')
    def ballooning_radius(self):
        p1 = self.prof1.data
        p2 = self.prof2.data
        phi = np.array(self.ballooning_phi)
        return np.linalg.norm(p1 - p2, axis=1) / (2 * np.sin(phi) + (phi == 0)) * (phi != 0)

    def copy(self):
        return copy.deepcopy(self)
