import math
import numpy
from dxfwrite import DXFEngine as dxf

from openglider.vector import normalize, norm
# from openglider.graphics import Graphics3D, Line


def export_obj(glider, path, midribs=0, numpoints=None, floatnum=6):
    other = glider.copy_complete()
    if numpoints:
        other.profile_numpoints = numpoints
    ribs = other.return_ribs(midribs)

    panels = []
    points = []
    numpoints = len(ribs[0])
    for i in range(len(ribs)):
        for j in range(numpoints):
            # Create two Triangles from one rectangle:
            # Start counting from 1; i->row; j->line
            panels.append([i * numpoints + j + 1, i * numpoints + j + 2,
                           (i + 1) * numpoints + j + 2])
            panels.append([(i + 1) * numpoints + j + 1, i * numpoints + j + 1,
                           (i + 1) * numpoints + j + 2])
            # Calculate normvectors
            # Y-Axis
            first = ribs[i + (i < len(ribs) - 1)][j] - ribs[i - (i > 0)][j]
            second = ribs[i][j - (j > 0)] - ribs[i][j + (j < numpoints - 1)]
            try:
                points.append(
                    (ribs[i][j], normalize(numpy.cross(first, second))))
            except ValueError:
                raise ValueError(
                    "vector of length 0 at: i={0}, j={1}: {2}".format(i, j,
                                                                      first))
    # TODO: check!?
    panels = panels[:2 * (len(ribs) - 1) * numpoints - 2]
    # Write file
    with open(path, "w") as outfile:
        for point in points:
            # point = point[0] * [-1, -1, -1], point[1] * [-1, -1, -1]
            # Write Normvector
            outfile.write("vn {0} {1} {2}\n".format(
                *map(lambda x: round(-x, floatnum), point[1])))
            # Write point
            outfile.write("v {0} {1} {2}\n".format(
                *map(lambda x: round(-x, floatnum), point[0])))
        for polygon in panels:
            outfile.write("f {0} {1} {2}//{0} {1} {2}\n".format(*polygon))
    return True


def export_json(glider, path, numpoints, midribs=0, wake_panels=1,
                wake_length=0.2, *other):
    """
    export json geometry file for panelmethod calculation
    """

    class Node():
        def __init__(self, p, n_id=None, is_wake=False):
            self.point = numpy.array(p)
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

        # This is just lazyness..
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

    glide_alpha = numpy.arctan(glider.glide)
    glider = glider.copy_complete()
    glider.profile_numpoints = numpoints
    rib_len = len(glider.ribs[0].profile_2d)

    v_inf = numpy.array([numpy.sin(glide_alpha), 0, numpy.cos(glide_alpha)])
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

    print(panels[10].is_wake, panels[10].neighbours[1].is_wake, panels[10].neighbours[3].is_wake)

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
    # write config
    outfile = open(path, "w")
    outfile.write("APAME input file\nVERSION 3.0\n")
    outfile.write("AIRSPEED " + str(other.data["GESCHWINDIGKEIT"]) + "\n")
    outfile.write(
        "DENSITY 1.225\nPRESSURE 1.013e+005\nMACH 0\nCASE_NUM 1\n")  # TODO: Multiple cases
    outfile.write(str(math.tan(1 / other.data["GLEITZAHL"])) + "\n0\n")
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
            outfile.write(u"1 {0!s}\t{1!s}\t{2!s}\t{3!s}\n".format(
                i * len(ribs[0]) + j + 1,
                (i + 1) * len(ribs[0]) + j + 1,
                (i + 1) * len(ribs[0]) + j + 2,
                i * len(ribs[0]) + j + 2))

    return outfile.close()


