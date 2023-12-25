import math
import numpy as np

# from openglider.graphics import Graphics3D, Line
from openglider.vector.functions import norm, normalize
from openglider.utils.distribution import Distribution


def export_obj(glider, path, midribs=0, numpoints=None, floatnum=6, copy=True):
    other = glider.copy_complete() if copy else glider
    if numpoints:
        other.profile_numpoints = numpoints

    mesh = other.get_mesh(midribs=midribs)
    mesh.export_obj(path)




def export_json(glider, path, numpoints, midribs=0, wake_panels=1,
                wake_length=0.2, *other):
    """
    export json geometry file for panelmethod calculation
    """

    class Node():
        def __init__(self, p, n_id=None, is_wake=False):
            self.point = np.array(p)
            self.n_id = n_id
            self.is_wake = is_wake

        def __json__(self):
            return self.point.tolist()

    class Panel():
        def __init__(self, nodes, p_id=None):
            self.nodes = nodes
            self.neighbours = [None, None, None, None]
            self.p_id = p_id

        @property
        def node_nos(self):
            return [node.n_id for node in self.nodes]

        @property
        def is_wake(self):
            return any([tha_node.is_wake for tha_node in self.nodes])

        # This is just laziness..
        def get_neighbours(self, panel_list):
            self.neighbours = [self.get_neighbour(self.nodes[0], self.nodes[1],
                                                  pan_list=panel_list),
                               self.get_neighbour(self.nodes[1], self.nodes[2],
                                                  pan_list=panel_list),
                               self.get_neighbour(self.nodes[2], self.nodes[3],
                                                  pan_list=panel_list),
                               self.get_neighbour(self.nodes[3], self.nodes[0],
                                                  pan_list=panel_list)]

        def get_neighbour(self, p1, p2, pan_list):
            for i, pan in enumerate(pan_list):
                if p1 in pan.nodes and p2 in pan.nodes and pan is not self:
                    return i
            return None

        def neighbour_ids(self):
            get_id = lambda p: p.p_id if p else p
            return [get_id(n) for n in self.neighbours]

        def __json__(self):
            return {"is_wake": self.is_wake,
                    "neighbours": self.neighbour_ids(),
                    "nodes": self.node_nos}

    glide_alpha = np.arctan(glider.glide)
    glider = glider.copy_complete()
    glider.profile_numpoints = numpoints
    rib_len = len(glider.ribs[0].profile_2d)

    v_inf = np.array([np.sin(glide_alpha), 0, np.cos(glide_alpha)])
    node_ribs = [[Node(node) for node in rib[1:]] for rib in
                 glider.return_ribs(midribs)]
    nodes_flat = []

    panel_ribs = []
    panels = []

    # Generate Wake
    for rib in node_ribs:
        rib += [
            Node(rib[-1].point + v_inf * (i + 1) / wake_panels * wake_length,
                 is_wake=True) for i in
            range(wake_panels)]
        # append to flat-list and >>calculate<< index
        for node in rib:
            node.n_id = len(nodes_flat)
            nodes_flat.append(node)

    # Generate Panels
    for left_rib, right_rib in zip(node_ribs[:-1], node_ribs[1:]):
        panel_rib = []
        pan = Panel([left_rib[0], left_rib[-wake_panels - 1],
                     right_rib[-wake_panels - 1], right_rib[0]],
                    p_id=len(panels))
        panel_rib.append(pan)
        panels.append(pan)
        for i in range(len(left_rib) - 1):
            pan = Panel([left_rib[i + 1], left_rib[i],
                         right_rib[i], right_rib[i + 1]],
                        p_id=len(panels))
            panels.append(pan)
            panel_rib.append(pan)
        panel_ribs.append(panel_rib)

    for i, row in enumerate(panel_ribs):
        for j, panel in enumerate(row):

            # left neighbour
            if i > 0 and not panel.is_wake:
                panel.neighbours[0] = panel_ribs[i - 1][j]
            else:
                panel.neighbours[0] = None
                # panel.neighbours[1] = row[rib_len-j-1]

            # back neighbour
            if j > 0 and j < rib_len - 1:
                panel.neighbours[1] = row[j - 1]
            else:
                panel.neighbours[1] = row[rib_len - 2]

            # right neighbour
            if i < len(panel_ribs) - 1 and not panel.is_wake:
                panel.neighbours[2] = panel_ribs[i + 1][j]
            else:
                panel.neighbours[2] = None
                #panel.neighbours[3] = row[rib_len - j - 1]

            # front neighbour
            if not panel.is_wake:
                panel.neighbours[3] = row[j + 1]
            else:
                panel.neighbours[3] = row[0]

    # for pan in panels:
    #    pan.get_neighbours(panels)
    #    pan.node_nos = [nodes_flat.index if tha_node is not None else None for tha_node in pan.nodes]

    #import openglider.graphics as graph
    #graph.Graphics([graph.Polygon([n.n_id for n in panel.nodes],
    #                              colour=[255, 255*(1-panel.is_wake), 255])
    #                for panel in panels],
    #               [n.point for n in nodes_flat])

    return {'nodes': [node.__json__() for node in nodes_flat],
            'panels': [panel.__json__() for panel in panels],
            'config': {'v_inf': v_inf.tolist(),
                       'coefficient': 6.,
                       'density': 1.2,
                       'pressure': 1.013,
                       'request_panels': True,
                       'request_nodes': True}}


def export_dxf(glider, path="", midribs=0, numpoints=None, *other):
    from dxfwrite import DXFEngine as dxf
    outfile = dxf.drawing(path)
    other = glider.copy_complete()
    if numpoints:
        other.profile_numpoints = numpoints
    ribs = other.return_ribs(midribs)
    panels = []
    points = []
    outfile.add_layer('RIBS', color=2)
    for rib in ribs:
        outfile.add(dxf.polyface(rib * 1000, layer='RIBS'))
        outfile.add(dxf.polyline(rib * 1000, layer='RIBS'))
    return outfile.save()


def export_apame(glider, path="", midribs=0, numpoints=None, *other):
    other = glider.copy_complete()
    if numpoints:
        other.profile_numpoints = numpoints
    ribs = other.return_ribs(midribs)
    v_inf = glider.lineset.v_inf
    speed = norm(v_inf)
    glide = np.arctan(v_inf[2]/v_inf[0])
    # write config
    outfile = open(path, "w")
    outfile.write("APAME input file\nVERSION 3.0\n")
    outfile.write("AIRSPEED {}\n".format(speed))
    outfile.write(
        "DENSITY 1.225\nPRESSURE 1.013e+005\nMACH 0\nCASE_NUM 1\n")  # TODO: Multiple cases
    outfile.write(str(math.tan(1 / glide)) + "\n0\n")
    outfile.write("WINGSPAN " + str(other.span) + "\n")
    outfile.write("MAC 2")  # TODO: Mean Choord
    outfile.write("SURFACE " + str(other.area) + "\n")
    outfile.write("ORIGIN\n0 0 0\n")
    outfile.write("METHOD 0\nERROR 1e-007\nCOLLDIST 1e-007\n")
    outfile.write("FARFIELD " + str(5) + "\n")  # TODO: farfield argument
    outfile.write(
        "COLLCALC 0\nVELORDER 2\nRESULTS 1\n1  1  1  1  1  1  1  1  1  1  1  1  1\n\n")
    outfile.write("NODES " + str(len(ribs) * len(ribs[0])) + "\n")

    for rib in ribs:
        for point in rib:
            for coord in point:
                outfile.write(str(coord) + "\t")
            outfile.write("\n")

    outfile.write("\nPANELS " + str((len(ribs) - 1) * (
        len(ribs[0]) - 1)) + "\n")  # TODO: ADD WAKE + Neighbours!
    for i in range(len(ribs) - 1):
        for j in range(other.profile_numpoints):
            # COUNTER-CLOCKWISE!
            outfile.write("1 {0!s}\t{1!s}\t{2!s}\t{3!s}\n".format(
                i * len(ribs[0]) + j + 1,
                (i + 1) * len(ribs[0]) + j + 1,
                (i + 1) * len(ribs[0]) + j + 2,
                i * len(ribs[0]) + j + 2))

    return outfile.close()


def parabem_Panels(glider, midribs=0, profile_numpoints=None, num_average=0, symmetric=False):
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
        ribs_ij = glider.return_ribs_ij(midribs)
    else:
        ribs = glider.return_ribs(midribs)
        ribs_ij = glider.return_ribs_ij(midribs)
    # deleting the last vertex of every rib (no trailing edge gap)
    ribs = [rib[:-1] for rib in ribs]
    # get a numbered representation + flatten vertices
    i = 0
    vertices = []
    ribs_new = []
    panels = []
    sym_panels = []
    trailing_edge = []
    mid_points_ij = []

    # computing the midpoints (for construction of a pressure interpolation,
    # which later can be used for fem computation)
    ribs_ij = np.array(ribs_ij)
    for rib_nr, rib_ij in enumerate(ribs_ij[:-1]):
        for x_nr, _ in enumerate(rib_ij[:-1]):
            p0 = ribs_ij[rib_nr, x_nr]
            p1 = ribs_ij[rib_nr, x_nr + 1]
            p2 = ribs_ij[rib_nr + 1, x_nr + 1]
            p3 = ribs_ij[rib_nr +1 , x_nr]
            mid_point = (p0 + p1 + p2 + p3) / 4
            mid_points_ij.append(mid_point)
    mid_points_ij = np.array(mid_points_ij)

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

    return vertices, panels, trailing_edge, mid_points_ij


def export_leparagliding(glider, path):
    import pandas as pd
    import jinja2

    ####### computing the basic geometry
    glider = glider.copy_complete()
    aoa_abs = np.array([r.aoa_absolute for r in glider.ribs])
    aoa_rel = np.array([r.aoa_relative for r in glider.ribs])
    gamma = np.arctan(1 / glider.glide)
    alpha_max = np.rad2deg(aoa_abs[0] + gamma)
    washin = np.rad2deg(aoa_abs)
    y_le, xp, z = np.array([r.pos for r in glider.ribs]).T * 1.0e2
    chord = np.array([r.chord for r in glider.ribs]) * 1.0e2
    y_te = y_le + chord
    x_rib = glider.shape_simple.front.data.T[0] * 1.0e2
    beta = np.rad2deg(np.array([r.arcang for r in glider.ribs]))
    rp = np.array([0.] * len(beta))
    ribs_number = np.array(list(range(len(rp))), dtype=int)
    data = { "Rib": ribs_number,
             "x_rib": x_rib,
             "y_LE": y_le,
             "y_TE": y_te,
             "xp": xp,
             "z": -z,
             "beta": beta,
             "RP": rp,
             "Washin": washin}
    data_frame = pd.DataFrame(data)
    if glider.has_center_cell:
        data_frame = data_frame[1:]
    rib_geo =  data_frame.to_string(index=None, float_format=lambda x: "{:.3f}".format(x))

    ############# exporting the glider

    env = jinja2.Environment(loader = jinja2.FileSystemLoader("."))
    template = env.get_template('leparagliding.txt.template')

    with open(path, 'w') as fn:
        fn.write(template.render(
            GR=glider.glide,
            alpha_max="{:.2f}".format(alpha_max),
            rib_geo=rib_geo,
            num_cells=len(glider.copy_complete().cells),
            num_ribs=len(glider.copy_complete().ribs)
        ))