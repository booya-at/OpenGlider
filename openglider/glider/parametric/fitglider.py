from __future__ import division

import numpy as np

from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.lines import LineSet2D
from openglider.glider.parametric.shape import ParametricShape
from openglider.vector import PolyLine2D, Interpolation
from openglider.vector.spline import SymmetricBezier, Bezier


def fit_glider_3d(cls, glider, numpoints=3):
    """
    Create a parametric model from glider
    """
    shape = glider.shape_simple
    front, back = shape.front, shape.back
    arc = [rib.pos[1:] for rib in glider.ribs]
    aoa = [[front[i][0], rib.aoa_relative] for i, rib in enumerate(glider.ribs)]
    zrot = [[front[i][0], rib.zrot] for i, rib in enumerate(glider.ribs)]

    def symmetric_fit(polyline, numpoints=numpoints):
        mirrored = PolyLine2D(polyline[1:]).mirror([0, 0], [0, 1])
        symmetric = mirrored[::-1].join(polyline[int(glider.has_center_cell):])
        return SymmetricBezier.fit(symmetric, numpoints=numpoints)

    front_bezier = symmetric_fit(front)
    back_bezier = symmetric_fit(back)
    arc_bezier = symmetric_fit(arc)
    aoa_bezier = symmetric_fit(aoa)
    zrot_bezier = symmetric_fit(zrot)

    cell_num = len(glider.cells) * 2 - glider.has_center_cell

    front[0][0] = 0  # for midribs
    start = (2 - glider.has_center_cell) / cell_num
    const_arr = [0.] + np.linspace(start, 1, len(front) - 1).tolist()

    rib_pos = [p[0] for p in front]
    cell_centers = [(p1+p2)/2 for p1, p2 in zip(rib_pos[:-1], rib_pos[1:])]

    rib_pos_int = Interpolation(zip([0] + rib_pos[1:], const_arr))
    rib_distribution = [[i, rib_pos_int(i)] for i in np.linspace(0, rib_pos[-1], 30)]
    rib_distribution = Bezier.fit(rib_distribution, numpoints=numpoints+3)

    profiles = [rib.profile_2d for rib in glider.ribs]
    profile_dist = Bezier.fit([[i, i] for i, rib in enumerate(front)],
                                   numpoints=numpoints)

    balloonings = [cell.ballooning for cell in glider.cells]
    ballooning_dist = Bezier.fit([[i, i] for i, rib in enumerate(front[1:])],
                                   numpoints=numpoints)

    zrot = Bezier([[0, 0], [front.last()[0], 0]])

    # TODO: lineset, dist-curce->xvalues

    parametric_shape = ParametricShape(front_bezier, back_bezier, rib_distribution, cell_num)
    parametric_arc = ArcCurve(arc_bezier)

    return cls(shape=parametric_shape,
               arc=parametric_arc,
               aoa=aoa_bezier,
               zrot=zrot_bezier,
               profiles=profiles,
               profile_merge_curve=profile_dist,
               balloonings=balloonings,
               ballooning_merge_curve=ballooning_dist,
               glide=glider.glide,
               speed=10,
               lineset=LineSet2D([]))
