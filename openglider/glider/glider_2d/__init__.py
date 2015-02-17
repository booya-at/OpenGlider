from __future__ import division

import scipy.interpolate
import numpy

from openglider.airfoil.parametric import BezierProfile2D
from openglider.glider import Glider
from openglider.glider.glider_2d.lines import Line2D, LineSet2D, UpperNode2D, \
                                              LowerNode2D, BatchNode2D
from openglider.vector import mirror2D_x
from openglider.utils.bezier import BezierCurve, SymmetricBezier
from openglider.vector.polyline import PolyLine2D
from openglider.vector.functions import norm, normalize, rotation_2d
from openglider.glider.rib import Rib
from openglider.glider.cell import Cell
from openglider.glider.cell_elements import Panel

from .lines import LowerNode2D, Line2D, LineSet2D, BatchNode2D, UpperNode2D
from .import_ods import import_ods_2d

class Glider2D(object):
    """
    A parametric (2D) Glider object used for gui input
    """
    def __init__(self, front, back, cell_dist, cell_num,
                 arc, aoa, profiles, profile_merge_curve,
                 balloonings, ballooning_merge_curve, lineset,
                 speed, glide):
        self.front = front
        self.back = back
        self.cell_num = cell_num  # updates cell pos
        self.cell_dist = cell_dist
        self.arc = arc
        self.aoa = aoa
        self.profiles = profiles or []
        self.profile_merge_curve = profile_merge_curve
        self.balloonings = balloonings or []
        self.ballooning_merge_curve = ballooning_merge_curve
        self.lineset = lineset or LineSet2D([], [])
        self.speed = speed
        self.glide = glide

    @classmethod
    def create_default(cls):
        front = SymmetricBezier()
        back = SymmetricBezier()
        cell_dist = BezierCurve()
        arc = BezierCurve()
        aoa = BezierCurve()

    def __json__(self):
        return {
            "front": self.front,
            "back": self.back,
            "cell_dist": self.cell_dist,
            "cell_num": self.cell_num,
            "arc": self.arc,
            "aoa": self.aoa,
            "profiles": self.profiles,
            "profile_merge_curve": self.profile_merge_curve,
            "balloonings": self.balloonings,
            "ballooning_merge_curve": self.ballooning_merge_curve,
            "lineset": self.lineset,
            "speed": self.speed,
            "glide": self.glide
        }

    @classmethod
    def import_ods(cls, path):
        return import_ods_2d(cls, path)

    @property
    def v_inf(self):
        angle = numpy.arctan(1/self.glide)
        return numpy.array([-numpy.cos(angle), 0, numpy.sin(angle)]) * self.speed

    @property
    def has_center_cell(self):
        return self.cell_num % 2

    def get_arc_positions(self, num=50):
        # calculating y/z values vor the arc-curve
        x_values = numpy.array(self.cell_dist_interpolation).T[0] #array of scalars
        
        arc_curve = PolyLine2D([self.arc(i) for i in numpy.linspace(0.5, 1, num)])  # Symmetric-Bezier-> start from 0.5
        arc_curve_length = arc_curve.get_length()
        _positions = [arc_curve.extend(0, x/x_values[-1]*arc_curve_length) for x in x_values]
        positions = PolyLine2D([arc_curve[p] for p in _positions])
        if not self.has_center_cell:
            positions[0][0] = 0
        # rescale
        return positions

    def get_arc_angles(self, arc_curve=None):
        # calculate rib rotations from arc
        arc_curve = arc_curve or self.get_arc_positions()
        arc_curve = [arc_curve[i] for i in range(len(arc_curve))]
        angles = []
        if not self.has_center_cell:
            angles.append(0)
        else:
            p0 = arc_curve[0]
            p_mirrored = [p0[0]*(-1), p0[1]]
            arc_curve.insert(0, p_mirrored)

        for i in range(len(arc_curve)-1):
            # before
            d = normalize(arc_curve[i+1]-arc_curve[i])
            if i+2 < len(arc_curve):
                # after
                d += normalize(arc_curve[i+2]-arc_curve[i+1])

            angles.append(numpy.arctan2(-d[1], d[0]))

        return angles

    def shape(self, num=30):
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        dist_line = self.cell_dist_interpolation
        dist = [i[0] for i in dist_line]
        front_line = [front_int(x) for x in dist]
        front = mirror2D_x(front_line)[::-1] + front_line
        back = [back_int(x) for x in dist]
        back = mirror2D_x(back)[::-1] + back
        ribs = zip(front, back)
        return [ribs, front, back]

    def ribs(self, num=30):         #property
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        dist_line = self.cell_dist_interpolation
        dist = [i[0] for i in dist_line]
        front = [front_int(x) for x in dist]
        back = [back_int(x) for x in dist]
        if self.has_center_cell:
            front.insert(0, [-front[0][0], front[0][1]])
            back.insert(0, [-back[0][0], back[0][1]])

        return zip(front, back)

    def shape_point(self, rib_no, x):
        ribs = list(self.ribs())
        rib = ribs[rib_no]
        return rib[0] + x * (rib[1] - rib[0])

    def set_span(self, span):
        """
        rescale BezierCurves
        """
        def set_span(attribute):
            el = getattr(self, attribute)
            assert el is not None, "Not a Beziercurve: {}".format(attribute)
            factor = span/el.controlpoints[-1][0]
            el.controlpoints = [[p[0]*factor, p[1]] for p in el.controlpoints]

        for attr in 'back', 'front', 'cell_dist', 'aoa', 'profile_merge_curve', 'ballooning_merge_curve':
            set_span(attr)

        arc_pos = self.get_arc_positions()
        arc_length = arc_pos.get_length() + arc_pos[0][0]  # add center cell
        factor = span/arc_length
        self.arc.controlpoints = [[p[0]*factor, p[1]*factor]
                                  for p in self.arc.controlpoints]

    @property
    def cell_dist_controlpoints(self):
        return self.cell_dist.controlpoints[1:-1]

    @cell_dist_controlpoints.setter
    def cell_dist_controlpoints(self, arr):
        self.cell_dist.controlpoints = [[0, 0]] + arr + [[self.front.controlpoints[-1][0], 1]]

    @property
    def cell_dist_interpolation(self):
        """
        Interpolate Cell-distribution
        """
        interpolation = self.cell_dist.interpolate_3d(num=20, axis=1)
        start = (self.has_center_cell) / self.cell_num
        return [interpolation(i) for i in numpy.linspace(start, 1, num=self.cell_num // 2 + 1)]

    def depth_integrated(self, num=100):
        """
        Return A(x)
        """
        x_values = numpy.linspace(0, self.front.controlpoints[-1][0], num)
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        integrated_depth = [0.]
        for x in x_values[1:]:
            integrated_depth.append(integrated_depth[-1] + 1. / (front_int(x)[1] - back_int(x)[1]))
        return zip(x_values, [i / integrated_depth[-1] for i in integrated_depth])

    @property
    def span(self):
        return self.cell_dist_interpolation[-1][0] * 2

    @property
    def attachment_points(self):
        """coordinates of the attachment_points"""
        return [a_p.get_2d(self) for a_p in self.lineset.nodes if isinstance(a_p, UpperNode2D)]

    def merge_ballooning(self, factor):
        factor = max(0, min(len(self.balloonings)-1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.balloonings[i]
        if k > 0:
            second = self.balloonings[i + 1]
            return first * (1 - k) + second * k
        else:
            return first.copy()

    def merge_profile(self, factor):
        factor = max(0, min(len(self.profiles)-1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.profiles[i]
        if k > 0:
            second = self.profiles[i + 1]
            return first * (1 - k) + second * k
        else:
            return first.copy()

    @classmethod
    def fit_glider_3d(cls, glider, numpoints=3):
        """
        Create a parametric model from glider
        """
        def mirror_x(polyline):
            mirrored = [[-p[0], p[1]] for p in polyline[1:]]
            return mirrored[::-1] + polyline[glider.has_center_cell:]

        front, back = glider.shape_simple
        arc = [rib.pos[1:] for rib in glider.ribs]
        aoa = [[front[i][0], rib.aoa_relative] for i, rib in enumerate(glider.ribs)]

        front_bezier = SymmetricBezier.fit(mirror_x(front), numpoints=numpoints)
        back_bezier = SymmetricBezier.fit(mirror_x(back), numpoints=numpoints)
        arc_bezier = SymmetricBezier.fit(mirror_x(arc), numpoints=numpoints)
        aoa_bezier = SymmetricBezier.fit(mirror_x(aoa), numpoints=numpoints)

        cell_num = len(glider.cells) * 2 - glider.has_center_cell

        front[0][0] = 0  # for midribs
        start = (2 - glider.has_center_cell) / cell_num
        const_arr = [0.] + numpy.linspace(start, 1, len(front) - 1).tolist()
        rib_pos = [0.] + [p[0] for p in front[1:]]
        rib_pos_int = scipy.interpolate.interp1d(rib_pos, [rib_pos, const_arr])
        rib_distribution = [rib_pos_int(i) for i in numpy.linspace(0, rib_pos[-1], 30)]
        rib_distribution = BezierCurve.fit(rib_distribution, numpoints=numpoints+3)

        profiles = [rib.profile_2d for rib in glider.ribs]
        profile_dist = BezierCurve.fit([[i, i] for i in range(len(profiles))],
                                       numpoints=numpoints)

        balloonings = [rib.ballooning for rib in glider.ribs]
        ballooning_dist = BezierCurve.fit([[i, i] for i in range(len(balloonings))],
                                       numpoints=numpoints)

        # TODO: lineset

        return cls(front=front_bezier,
                   back=back_bezier,
                   cell_dist=rib_distribution,
                   cell_num=cell_num,
                   arc=arc_bezier,
                   aoa=aoa_bezier,
                   profiles=profiles,
                   profile_merge_curve=profile_dist,
                   balloonings=balloonings,
                   ballooning_merge_curve=ballooning_dist,
                   glide=glider.glide,
                   speed=10,
                   lineset=LineSet2D([]))

    def get_glider_3d(self, glider=None, num=50):
        """returns a new glider from parametric values"""
        glider = glider or Glider()
        ribs = []
        cells = []

        span = self.front.controlpoints[-1][0]
        self.set_span(span)

        x_values = [rib_no[0] for rib_no in self.cell_dist_interpolation]
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        profile_merge_curve = self.profile_merge_curve.interpolate_3d(num=num)
        ballooning_merge_curve = self.ballooning_merge_curve.interpolate_3d(num=num)
        aoa_int = self.aoa.interpolate_3d(num=num)

        arc_pos = list(self.get_arc_positions(num=num))
        arc_angles = self.get_arc_angles()

        profile_x_values = self.profiles[0].x_values

        if x_values[0] != 0.:
            # adding the mid cell
            x_values = [-x_values[0]] + x_values
            arc_pos = [[-arc_pos[0][0], arc_pos[0][1]]] + arc_pos
            arc_angles = [-arc_angles[0]] + arc_angles

        for rib_no, pos in enumerate(x_values):
            front = front_int(pos)
            back = back_int(pos)
            arc = arc_pos[rib_no]
            factor = profile_merge_curve(abs(pos))[1]
            profile = self.merge_profile(factor)
            profile.x_values = profile_x_values

            ribs.append(Rib(
                profile_2d=profile,
                ballooning=self.merge_ballooning(ballooning_merge_curve(abs(pos))[1]),
                startpoint=numpy.array([-front[1], arc[0], arc[1]]),
                chord=norm(front - back),
                arcang=arc_angles[rib_no],
                glide=self.glide,
                aoa_absolute=aoa_int(pos)[1]
            ))
            ribs[-1].aoa_relative = aoa_int(pos)[1]

        for rib_no, rib in enumerate(ribs[1:]):
            cell = Cell(ribs[rib_no], rib, [])
            cell.panels = [Panel([-1, -1, 3, 0.012], [1, 1, 3, 0.012], rib_no)]
            cells.append(cell)
            glider.cells = cells

        glider.close_rib()

        glider.lineset = self.lineset.return_lineset(glider, self.v_inf)
        glider.lineset.calc_geo()
        glider.lineset.calc_sag()
        return glider

    @property
    def v_inf(self):
        angle = numpy.arctan(1/self.glide)
        return self.speed * numpy.array([numpy.cos(angle), 0, numpy.sin(angle)])
