import math

__author__ = 'simon'
from openglider.Vector import normalize, norm
import numpy
from dxfwrite import DXFEngine as dxf
from openglider.Graphics import Graphics3D, Line


def export_obj(glider, path, midribs=0, numpoints=None, floatnum=6):
    other = glider.copy()
    if numpoints:
        other.numpoints = numpoints
        print(other.numpoints)
    other.mirror()
    other.cells[-1].rib2 = glider.cells[0].rib1
    other.cells = other.cells + glider.cells
    other.recalc()
    ribs = other.return_ribs(midribs)

    panels = []
    points = []
    numpoints = len(ribs[0])
    for i in range(len(ribs)):
        for j in range(numpoints):
            # Create two Triangles from one rectangle:
            # rectangle: [i * numpoints + k, i * numpoints + k + 1, (i + 1) * numpoints + k + 1, (i + 1) * numpoints + k])
            # Start counting from 1!!
            panels.append([i * numpoints + j + 1, i * numpoints + j + 2, (i + 1) * numpoints + j + 2])
            panels.append([(i + 1) * numpoints + j + 1, i * numpoints + j + 1, (i + 1) * numpoints + j + 2])
            # Calculate normvectors
            first = ribs[i + (i < len(ribs) - 1)][j] - ribs[i - (i > 0)][j]  # Y-Axis
            #if norm(first) == 0:  # TODO: JUst a quick fix, find the problem!! it seems to be in the center
            #    first = ribs[i+2*(i < len(ribs)-2)][j] - ribs[i-2*(i > 1)][j]
            second = ribs[i][j - (j > 0)] - ribs[i][j + (j < numpoints - 1)]
            try:
                points.append((ribs[i][j], normalize(numpy.cross(first, second))))
            except ValueError:
                raise ValueError("vektor of length 0 at: i=" + str(i) + ", j=" + str(j) + str(first))
    panels = panels[:2 * (len(ribs) - 1) * numpoints - 2]
    # Write file
    outfile = open(path, "w")
    for point in points:
        point = point[0] * [-1, -1, -1], point[1] * [-1, -1, -1]
        outfile.write("vn")
        for coord in point[1]:
            outfile.write(" " + str(round(coord, floatnum)))
        outfile.write("\n")
        outfile.write("v")
        for coord in point[0]:
            outfile.write(" " + str(round(coord, floatnum)))
        outfile.write("\n")
        #outfile.write("# "+str(len(points))+" vertices, 0 vertices normals\n\n")
    for polygon in panels:
        outfile.write("f")
        for point in polygon:
            outfile.write(" " + str(point) + "//" + str(point))
        outfile.write("\n")
        #outfile.write("# "+str(len(panels))+" faces, 0 coords texture\n\n# End of File")
    #print(len(points), len(normvectors), len(panels), max(panels, key=lambda x: max(x)))

    outfile.close()
    return True


def export_dxf(glider, path="", midribs=0, numpoints=None, *other):
    outfile = dxf.drawing(path)
    other = glider.copy()
    if numpoints:
        other.numpoints = numpoints
    other.mirror()
    other.cells[-1].rib2 = glider.cells[0].rib1
    other.cells = other.cells + glider.cells
    other.recalc()
    ribs = other.return_ribs(midribs)
    panels = []
    points = []
    outfile.add_layer('RIBS', color=2)
    for rib in ribs:
        outfile.add(dxf.polyface(rib * 1000, layer='RIBS'))
        outfile.add(dxf.polyline(rib * 1000, layer='RIBS'))
    return outfile.save()


def export_apame(glider, path="", midribs=0, numpoints=None, *other):
    other = glider.copy()
    other.mirror()
    other.cells[-1].rib2 = glider.cells[0].rib1
    other.cells = other.cells + glider.cells
    if numpoints:
        other.numpoints = numpoints
    other.recalc()
    ribs = other.return_ribs(midribs)
    #write config
    outfile = open(path, "w")
    outfile.write("APAME input file\nVERSION 3.0\n")
    outfile.write("AIRSPEED " + str(glider.data["GESCHWINDIGKEIT"]) + "\n")
    outfile.write("DENSITY 1.225\nPRESSURE 1.013e+005\nMACH 0\nCASE_NUM 1\n")  # TODO: Multiple cases
    outfile.write(str(math.tan(1 / glider.data["GLEITZAHL"])) + "\n0\n")
    outfile.write("WINGSPAN " + str(glider.span) + "\n")
    outfile.write("MAC 2") # TODO: Mean Choord
    outfile.write("SURFACE " + str(glider.area) + "\n")
    outfile.write("ORIGIN\n0 0 0\n")
    outfile.write("METHOD 0\nERROR 1e-007\nCOLLDIST 1e-007\n")
    outfile.write("FARFIELD " + str(5) + "\n")  # TODO: farfield argument
    outfile.write("COLLCALC 0\nVELORDER 2\nRESULTS 1\n1  1  1  1  1  1  1  1  1  1  1  1  1\n\n")
    outfile.write("NODES " + str(len(ribs) * len(ribs[0])) + "\n")

    for rib in ribs:
        for point in rib:
            for coord in point:
                outfile.write(str(coord) + "\t")
            outfile.write("\n")

    outfile.write("\nPANELS " + str((len(ribs) - 1) * (len(ribs[0]) - 1)) + "\n")  # TODO: ADD WAKE + Neighbours!
    for i in range(len(ribs) - 1):
        for j in range(other.numpoints):
            # COUNTER-CLOCKWISE!
            outfile.write(u"1 {0!s}\t{1!s}\t{2!s}\t{3!s}\n".format(i * len(ribs[0]) + j + 1,
                                                                   (i + 1) * len(ribs[0]) + j + 1,
                                                                   (i + 1) * len(ribs[0]) + j + 2,
                                                                   i * len(ribs[0]) + j + 2))

    return outfile.close()


