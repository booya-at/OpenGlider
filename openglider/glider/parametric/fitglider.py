from __future__ import division

import numpy as np
import euklid

from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.lines import LineSet2D
from openglider.glider.parametric.shape import ParametricShape


def fit_glider_3d(cls, glider, numpoints=3):
    """
    Create a parametric model from glider
    """
    shape = glider.shape_simple
    front, back = shape.front, shape.back
    arc = [rib.pos[1:] for rib in glider.ribs]
    aoa = [[front.get(i)[0], rib.aoa_relative] for i, rib in enumerate(glider.ribs)]
    zrot = [[front.get(i)[0], rib.zrot] for i, rib in enumerate(glider.ribs)]

    def symmetric_fit(polyline, numpoints=numpoints):
        return euklid.vector.SymmetricBSplineCurve.fit(polyline, numpoints)

    front_bezier = symmetric_fit(front)
    back_bezier = symmetric_fit(back)
    arc_bezier = symmetric_fit(arc)
    aoa_bezier = symmetric_fit(aoa)
    zrot_bezier = symmetric_fit(zrot)

    cell_num = len(glider.cells) * 2 - glider.has_center_cell

    front.get(0)[0] = 0  # for midribs
    start = (2 - glider.has_center_cell) / cell_num
    const_arr = [0.] + np.linspace(start, 1, len(front) - 1).tolist()

    rib_pos = [p[0] for p in front]

    rib_pos_int = euklid.vector.Interpolation(list(zip([0] + rib_pos[1:], const_arr)))
    rib_distribution = [[i, rib_pos_int.get_value(i)] for i in np.linspace(0, rib_pos[-1], 30)]
    rib_distribution = euklid.vector.BSplineCurve.fit(rib_distribution, numpoints+3)

    profiles = [rib.profile_2d for rib in glider.ribs]
    profile_dist = euklid.vector.BSplineCurve.fit([[i, i] for i, rib in enumerate(front)],
                                   numpoints)

    balloonings = [cell.ballooning for cell in glider.cells]
    ballooning_dist = euklid.vector.BSplineCurve.fit([[i, i] for i, rib in enumerate(front.nodes[1:])],
                                   numpoints)

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
