from __future__ import division
import copy
import math
import numpy as np
import euklid

from openglider.airfoil import Profile3D
from openglider.utils.cache import CachedObject, cached_property
from openglider.vector import normalize, norm


class BasicCell(CachedObject):
    """
    A very simple cell without any extras like midribs, diagonals,..
    """
    def __init__(self, prof1=None, prof2=None, ballooning=None, name="unnamed_cell"):
        self.prof1: Profile3D = prof1 or Profile3D([])
        self.prof2: Profile3D = prof2 or Profile3D([])

        if ballooning is not None:
            self.ballooning_phi = ballooning  # ballooning arcs -> property in cell
        self.name = name

    def point_basic_cell(self, y=0, ik=0):
        ##round ballooning
        return self.midrib(y).point(ik)

    def midrib(self, y_value, ballooning=True, arc_argument=True, with_numpy=True, close_trailing_edge=False):
        if y_value <= 0:              # left side
            return self.prof1
        elif y_value >= 1:            # right side
            return self.prof2
        else:                   # somewhere else
            #self._checkxvals()
            midrib = []

            # Ballooning is considered to be arcs, following 2 (two!) simple rules:
            # 1: x1 = x*d
            # 2: x2 = R*normvekt*(cos(phi2)-cos(phi)
            # 3: norm(d)/r*(1-x) = 2*sin(phi(2))
            if with_numpy:
                prof1 = np.array(self.prof1.curve.tolist())
                prof2 = np.array(self.prof2.curve.tolist())

                phi = np.array(self.ballooning_phi)
                normals = np.array(self.normvectors)
                radius = np.array(self.ballooning_radius)

                phi = phi  + (1e-10 - phi) * (phi <= 0.)  # => phi = min(phi, 1e-10)
                psi = phi * 2 * y_value
                l_h = np.cos(phi - psi) - np.cos(phi)
                l_d = 0.5 * (1 - np.sin(phi - psi) / np.sin(phi))
                radius = radius * (radius > 0.)  # => radius = min(radius, 0)
                midrib = prof1.T - l_d * (prof1 - prof2).T + (l_h * radius) * normals.T
                return Profile3D(midrib.T.tolist())

            for i in range(len(self.prof1.curve.nodes)):  # Arc -> phi(bal) -> r  # oder so...
                diff = self.prof1.curve.nodes[i] - self.prof2.curve.nodes[i]
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
        prof1 = self.prof1.curve
        prof2 = self.prof2.curve
        
        t_1 = self.prof1.tangents
        t_2 = self.prof2.tangents
        # cross differenzvektor, tangentialvektor

        normals = []

        for p1, p2, t1, t2 in zip(prof1, prof2, t_1, t_2):
            normal = (t1 + t2).cross(p1 - p2)
            normals.append(normal.normalized())
        
        return normals

    @cached_property('ballooning_phi')
    def ballooning_cos_phi(self):
        tolerance = 0.00001
        phi = np.array(self.ballooning_phi)
        return np.cos(phi)

    @cached_property('ballooning_phi', 'prof1', 'prof2')
    def ballooning_radius(self):
        prof1 = self.prof1.curve
        prof2 = self.prof2.curve

        phi = np.array(self.ballooning_phi)

        radius = []

        for p1, p2, phi in zip(prof1, prof2, self.ballooning_phi):
            r = (p1-p2).length() / (2 * math.sin(phi) + (phi==0))

            radius.append(r*(phi != 0))

        return radius

    def copy(self):
        return copy.deepcopy(self)
