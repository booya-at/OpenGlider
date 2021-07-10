import math
import numpy as np

# from openglider.graphics import Graphics3D, Line
from openglider.utils.distribution import Distribution


def export_obj(glider, path, midribs=0, numpoints=None, floatnum=6, copy=True):
    other = glider.copy_complete() if copy else glider
    if numpoints:
        other.profile_numpoints = numpoints

    mesh = other.get_mesh(midribs=midribs)
    mesh.export_obj(path)


def parabem_Panels(glider, midribs=0, profile_numpoints=None, num_average=0, symmetric=False, distribution=None):
    """return the vertices, panels and the trailing edge of a glider, as parabem objects.

    midribs:           midribs of a cell spanwise. if num_average is greater then
                       0 ballooning will be disables
    profile_numpoints: coordinates of every rib, choordwise
    num_average:       steps to average a cell profile
    symmetric:         set to True if a symmetric result is expected (this will
                       reduce evaluation time)
    """
    # parabem is not a dependency of openglider so if problems occur here, get the module.
    import parabem

    if symmetric:
        glider = glider.copy()
    else:
        glider = glider.copy_complete()
        glider.close_rib(0)
    glider.close_rib()

    if profile_numpoints:
        glider.profile_x_values = Distribution.from_nose_cos_distribution(profile_numpoints, 0.2)

    if num_average > 0:
        glider.apply_mean_ribs(num_average)
        glider.close_rib()
        ribs = glider.return_ribs(midribs, ballooning=False)
    else:
        ribs = glider.return_ribs(midribs)
    # deleting the last vertex of every rib (no trailing edge gap)
    ribs = [rib[:-1] for rib in ribs]
    # get a numbered representation + flatten vertices
    i = 0
    vertices = []
    ribs_new = []
    panels = []
    sym_panels = []
    trailing_edge = []

    for rib in ribs:
        rib_new = []
        for vertex in rib:
            rib_new.append(i)
            vertices.append(vertex)
            i += 1
        rib_new.append(rib_new[0])
        ribs_new.append(rib_new)
    ribs = ribs_new
    panel_nr = 0
    for i, rib_i in enumerate(ribs[:-1]):
        rib_j = ribs[i+1]
        if symmetric:
            if vertices[rib_j[0]][1] > 0.00001:
                trailing_edge.append(rib_i[0])
        else:
            trailing_edge.append(rib_i[0])
        if i == len(ribs[:-2]):
            trailing_edge.append(rib_j[0])

        for k, _ in enumerate(rib_j[:-1]):
            l = k + 1
            panel = [rib_i[k], rib_j[k], rib_j[l], rib_i[l]]
            if symmetric:
                sym = True
                add_panel = False
                for p in panel:
                    if not vertices[p][1] > -0.000001:      # if one point lies on the y- side
                        sym = False                         # y- is the mirrored side
                    if not vertices[p][1] < 0.0001:      # if one point lies on the y+ side
                        add_panel = True
                if add_panel:
                    panels.append(panel)
                    if sym:
                        sym_panels.append(panel_nr)
                    panel_nr += 1
            else:
                panels.append(panel)

    vertices = [parabem.PanelVector3(*point) for point in vertices]
    panels = [parabem.Panel3([vertices[nr] for nr in panel]) for panel in panels]
    trailing_edge = [vertices[nr] for nr in trailing_edge]
    for nr in sym_panels:
        panels[nr].set_symmetric()

    return vertices, panels, trailing_edge

