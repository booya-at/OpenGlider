from typing import List
import os
import re
import math
import tempfile
import shutil
import logging

import euklid
import numpy as np

from openglider.utils.cache import HashedList
from openglider.utils.distribution import Distribution


logger = logging.getLogger(__name__)


class Profile2D:
    noseindex: int
    name: str
    """
    Profile2D: 2 Dimensional Standard airfoil representative
    """
    def __init__(self, data, name="unnamed") -> None:
        self.name = name
        self.curve = euklid.vector.PolyLine2D(data)
        self._setup()

    def _setup(self):
        i = 0
        data = self.curve.nodes
        while data[i + 1][0] < data[i][0] and i < len(data):
            i += 1
        self.noseindex = i

        # Create a mapping x -> ik value
        self._interpolation_x_values = euklid.vector.Interpolation(
            [[-p[0], i] for i, p in enumerate(self.curve.nodes[:self.noseindex])] +
            [[ p[0], i+self.noseindex] for i, p in enumerate(self.curve.nodes[self.noseindex:])]
        )

    def __mul__(self, value) -> "Profile2D":
        fakt = euklid.vector.Vector2D([1, float(value)])

        return Profile2D(self.curve * fakt)

    def __call__(self, xval) -> float:
        return self.get_ik(xval)

    def get_ik(self, x) -> float:
        xval = float(x)
        return self._interpolation_x_values.get_value(xval)
    
    def get(self, x) -> euklid.vector.Vector2D:
        ik = self.get_ik(x)
        return self.curve.get(ik)

    def align(self, p) -> euklid.vector.Vector2D:
        """Align a point (x, y) on the airfoil. x: (0,1), y: (-1,1)"""
        x, y = p

        upper = self.get(-x)
        lower = self.get(x)

        return lower + (upper-lower) * ((y + 1)/2)

    def profilepoint(self, xval, h=-1.) -> euklid.vector.Vector2D:
        """
        Get airfoil Point for x-value (<0:upper side)
        optional: height (-1:lower,1:upper)
        """
        if h == -1:
            return self.get(xval)
        else:
            return self.align([xval, h])

    def normalized(self, close=True) -> "Profile2D":
        """
        Normalize the airfoil.
        This routine does:
            *Put the nose back to (0,0)
            *De-rotate airfoil
            *Reset its length to 1
        """
        nose = self.curve.nodes[self.noseindex]

        new_curve = self.curve.move(nose * -1)

        diff = (new_curve.nodes[0] + new_curve.nodes[-1]) * 0.5
        diff_sq = diff.dot(diff)

        v1 = euklid.vector.Vector2D([0, -1])
        v2 = euklid.vector.Vector2D([1,0])
        
        sin_sq = diff.dot(v1) / diff_sq  # Angle: a.b=|a|*|b|*sin(alpha)
        cos_sq = diff.dot(v2) / diff_sq
        matrix = np.array([[cos_sq, -sin_sq], [sin_sq, cos_sq]])  # de-rotate and scale
        
        data = np.array([matrix.dot(i) for i in new_curve]).tolist()

        if close:
            data[0][1] = 0
            data[-1][1] = 0
        
        return Profile2D(data)
    
    @property
    def normvectors(self) -> euklid.vector.PolyLine2D:
        return self.curve.normvectors()

    def copy(self) -> "Profile2D":
        new_name = f"{self.name}_copy"
        return Profile2D(self.curve.nodes, new_name)

    def get_data(self, negative_x=False):
        if not negative_x:
            return self.data
        else:
            data = np.array(self.data)
            data[:,0] *= np.array([-1.] * self.noseindex + [1.] * (len(self) - self.noseindex))
            return data

    def __add__(self, other, conservative=False):
        """
        Mix 2 Profiles
        """
        new = []
        for i, point in enumerate(self.curve.nodes):
            x = point[0]
            if i < self.noseindex:
                x = -x

            y2 = other.get(x)[1]
            new.append(point + [0, y2])
        
        return Profile2D(new)

    def __json__(self):
        return {
            "data": [list(p) for p in self.curve.nodes],
            "name": self.name
        }

    _re_number = r"([-+]?\d*\.\d*(?:[eE][+-]?\d+)?|\d+)"
    _re_coord_line = re.compile(rf"\s*{_re_number}\s+{_re_number}\s*")

    @classmethod
    def import_from_dat(cls, path) -> "Profile2D":
        """
        Import an airfoil from a '.dat' file
        """
        name = os.path.split(path)[-1]
        with open(path, "r") as p_file:
            return cls._import_dat(p_file, name=name)
    
    @classmethod
    def _import_dat(cls, p_file, name="unnamed") -> "Profile2D":
        profile = []
        for i, line in enumerate(p_file):
            if line.endswith(","):
                line = line[:-1]

            match = cls._re_coord_line.match(line)

            if match:
                profile.append([float(i) for i in match.groups()])
            elif i == 0:
                name = line.strip()
            else:
                logger.error(f"error in dat airfoil: {name} {i}:({line.strip()})")

        return cls(profile, name)


    def export_dat(self, pfad) -> str:
        """
        Export airfoil to .dat Format
        """
        with open(pfad, "w") as out:
            if self.name:
                out.write(str(self.name).strip())
            for p in self.curve.nodes:
                out.write("\n{: 10.8f}\t{: 10.8f}".format(*p))
        return pfad


    @classmethod
    def compute_trefftz(cls, m=-0.1+0.1j, tau=0.05, numpoints=100) -> "Profile2D":
        from openglider.airfoil.conformal_mapping import TrefftzKuttaAirfoil
        airfoil = TrefftzKuttaAirfoil(midpoint=m, tau=tau)
        nodes = [[c.real, c.imag] for c in airfoil.coordinates(numpoints)]

        # find the smallest xvalue to reset the nose
        profile = cls(nodes, "TrefftzKuttaAirfoil_m=" + str(m) + "_tau=" + str(tau))
        profile = profile.normalized()
        return profile

    #@cached_property('self')
    @property
    def x_values(self) -> List[float]:
        """Get XValues of airfoil. upper side neg, lower positive"""
        i = self.noseindex

        x_values = [-vector[0] for vector in self.curve.nodes[:i]]
        x_values += [vector[0] for vector in self.curve.nodes[i:]]
        return x_values

    def set_x_values(self, xval):
        """Set X-Values of airfoil to defined points."""
        new_nodes = [
            self.get(x) for x in xval
        ]

        return Profile2D(new_nodes)

    @property
    def numpoints(self):
        return len(self.curve.nodes)

    def set_numpoints(self, numpoints):
        x_values = Distribution.from_cos_distribution(numpoints)

        return self.set_x_values(x_values)

    @property
    def thickness(self):
        """return the maximum sickness (Sic!) of an airfoil"""
        xvals = sorted(set(map(abs, self.x_values)))

        return max([
            abs(self.get(-x)[1] - self.get(x)[1]) for x in xvals
        ])

    def set_thickness(self, newthick):
        factor = float(newthick / self.thickness)

        name = self.name
        if name is not None:
            name += "_" + str(newthick) + "%"

        return Profile2D(self.curve * [1, factor])

    @property
    def camber_line(self):
        xvals = sorted(set(map(abs, self.x_values)))
        return euklid.vector.PolyLine2D([self.profilepoint(i, 0.) for i in xvals])

    #@cached_property('self')
    @property
    def camber(self):
        """return the maximum camber of the airfoil"""
        return max([p[1] for p in self.camber_line])

    def set_camber(self, newcamber):
        """Set maximal camber to the new value"""
        old_camber = self.camber
        factor = newcamber / old_camber - 1
        now = dict(self.camber_line)

        data = [p + [0, now[p[0]] * factor] for p in self.curve.nodes]

        return Profile2D(data)

    @property
    def has_zero_thickness(self):
        # big problem when used with flap
        data = self.curve.nodes

        for _x, y in data:
            if abs(y) > 0.0001:
                return False
        return True

    @property
    def upper_indices(self):
        return range(0, self.noseindex)

    @property
    def lower_indices(self):
        return range(self.noseindex + 1, len(self))

    def insert_point(self, pos, tolerance=1e-5):
        nearest_x_value = self.nearest_x_value(pos)
        new_nodes = self.curve.nodes[:]

        if abs(nearest_x_value - pos) > tolerance:
            point = self.get(pos)
            ik = self.get_ik(pos)

            new_nodes.insert(int(ik + 1), point)

        return Profile2D(new_nodes)

    def remove_points(self, start, end, tolerance=0.):
        new_data = []

        ik_start = self.get_ik(start)
        ik_end = self.get_ik(end)

        i_start = int(ik_start - ik_start%1)
        if (self.curve.get(ik_start)-self.curve.get(i_start)).length() > tolerance:
            i_start += 1
        
        i_end = int(ik_end - ik_end%1)
        if (self.curve.get(ik_end)-self.curve.get(i_end+1)).length() <= tolerance:
            i_end += 1

        new_data = self.curve.nodes[:i_start+1] + self.curve.nodes[i_end:]
        
        return Profile2D(new_data)

    def move_nearest_point(self, pos):
        ik = self(pos)
        diff = ik % 1.
        if diff < 0.5:
            i = int(ik)
        else:
            i = int(ik)+1

        new_nodes = self.curve.nodes[:i-1]
        new_nodes.append(self.profilepoint(pos))
        new_nodes += self.curve.nodes[i:]

        return Profile2D(new_nodes)

    def nearest_x_value(self, x):
        ik = self.get_ik(x)

        diff = ik % 1.
        if diff < 0.5:
            i = int(ik)
        else:
            i = int(ik)+1
        
        result = self.curve.get(i)[0]

        if x < 0:
            result = -result
        return result

    def apply_function(self, foo):
        data = np.array(self.data)
        self.data = [foo(i, upper=index < self.noseindex) for index, i in enumerate(data)]

    @classmethod
    def from_url(cls, name='atr72sm', url='http://m-selig.ae.illinois.edu/ads/coord/'):
        import urllib.request
        airfoil_name = name + '.dat'
        temp_name = os.path.join(tempfile.gettempdir(), airfoil_name)
        with urllib.request.urlopen(url + airfoil_name) as data_file, open(temp_name, 'w') as dat_file:
            dat_file.write(data_file.read().decode('utf8'))

        return cls.import_from_dat(temp_name)

    def set_flap(self, flap_begin, flap_amount):
        @np.vectorize
        def f(x, a, b):
            c1, c2, c3 = -a**2*b/(a**2 - 2*a + 1), 2*a*b/(a**2 - 2*a + 1), -b/(a**2 - 2*a + 1)
            if x < a:
                return 0.
            if x > 1:
                return -b
            return c1 + c2 * x + c3 * x**2

        x, y = np.array(self.curve.nodes).T
        dy = f(x, flap_begin, flap_amount)
        
        data = np.array([x, y + dy]).T

        return Profile2D(data.tolist())

    @classmethod
    def compute_naca(cls, naca=1234, numpoints=100):
        """Compute and return a four-digit naca-airfoil"""
        # See: http://people.clarkson.edu/~pmarzocc/AE429/The%20NACA%20airfoil%20series.pdf
        # and: http://airfoiltools.com/airfoil/naca4digit
        m = int(naca / 1000) * 0.01  # Maximum Camber Position
        p = int((naca % 1000) / 100) * 0.1  # second digit: Maximum Thickness position
        t = (naca % 100) * 0.01  # last two digits: Maximum Thickness(%)
        x_values = [1-math.sin((x * 1. / (numpoints-1)) * math.pi / 2) for x in range(numpoints)]
        #x_values = self.cos_distribution(numpoints)

        upper = []
        lower = []
        a0 = 0.2969
        a1 = -0.126
        a2 = -0.3516
        a3 = 0.2843
        a4 = -0.1015

        for x in x_values:
            if x < p:
                mean_camber = (m / (p ** 2) * (2 * p * x - x ** 2))
                gradient = 2 * m / (p ** 2) * (p - x)
            else:
                mean_camber = (m / ((1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x ** 2))
                gradient = 2 * m / (1 - p ** 2) * (p - x)

            thickness_this = t / 0.2 * (a0 * math.sqrt(x) + a1 * x + a2 * x ** 2 + a3 * x ** 3 + a4 * x ** 4)
            #theta = math.atan(gradient)
            costheta = (1 + gradient ** 2) ** (-0.5)
            sintheta = gradient * costheta
            upper.append([x - thickness_this * sintheta,
                          mean_camber + thickness_this * costheta])
            lower.append([x + thickness_this * sintheta,
                          mean_camber - thickness_this * costheta])
        return cls(upper + lower[::-1][1:], name="NACA_" + str(naca))

    @classmethod
    def compute_joukowsky(cls, m=-0.1+0.1j, numpoints=100):
        from openglider.airfoil.conformal_mapping import JoukowskyAirfoil
        airfoil = JoukowskyAirfoil(m)
        profile = [[c.real, c.imag] for c in airfoil.coordinates(numpoints)]

        profile = cls(profile, "joukowsky_" + str(m)).normalized()
        profile.numpoints = numpoints
        return profile

    @classmethod
    def compute_vandevooren(cls, tau=0.05, epsilon=0.05, numpoints=100):
        from openglider.airfoil.conformal_mapping import VanDeVoorenAirfoil
        airfoil = VanDeVoorenAirfoil(tau=tau, epsilon=epsilon)
        profile = [[c.real, c.imag] for c in airfoil.coordinates(numpoints)]

        # find the smallest xvalue to reset the nose
        profile = cls(profile, "VanDeVooren_tau=" + str(tau) + "_epsilon=" + str(epsilon))
        
        profile = profile.normalized()
        profile.numpoints = numpoints
        return profile
    
    def _repr_svg_(self):
        import svgwrite
        dwg = svgwrite.Drawing('test.svg')

        y = [p[1] for p in self.curve.nodes]

        ymin = min(y)
        ymax = max(y)
        height = ymax - ymin
        dwg.viewbox(-0.1, ymin-0.1, 1.2, height+0.2)

        group = svgwrite.container.Group()
        group.scale(1, -1)  # svg coordinate system is x->right y->down


        style = svgwrite.container.Style()
        style.append("\nline { vector-effect: non-scaling-stroke; stroke-width: 1; fill: none}")
        style.append("\npolyline { vector-effect: non-scaling-stroke; stroke-width: 1; fill: none}")

        pl=svgwrite.shapes.Polyline(self.curve.tolist(), stroke= "black", stroke_width= 0.25)
        group.add(pl)
        group.add(svgwrite.shapes.Polyline(
            self.camber_line.tolist(), stroke="red", stroke_width=0.25
        ))
        
        dwg.add(group)
        dwg.defs.add(style)
        
        return dwg.tostring()