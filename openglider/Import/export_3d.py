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
            panels.append([i*numpoints + j+1, i*numpoints + j+2, (i+1)*numpoints + j+2])
            panels.append([(i+1)*numpoints + j+1, i*numpoints + j+1, (i+1)*numpoints + j+2])
            # Calculate normvectors
            first = ribs[i+(i < len(ribs)-1)][j] - ribs[i-(i > 0)][j]  # Y-Axis
            #if norm(first) == 0:  # TODO: JUst a quick fix, find the problem!! it seems to be in the center
            #    first = ribs[i+2*(i < len(ribs)-2)][j] - ribs[i-2*(i > 1)][j]
            second = ribs[i][j-(j > 0)]-ribs[i][j+(j < numpoints-1)]
            try:
                points.append((ribs[i][j], normalize(numpy.cross(first, second))))
            except ValueError:
                raise ValueError("vektor of length 0 at: i="+str(i)+", j="+str(j)+str(first))
    panels = panels[:2*(len(ribs)-1)*numpoints-2]
    # Write file
    outfile = open(path, "w")
    for point in points:
        point = point[0]*[-1, -1, -1], point[1]*[-1, -1, -1]
        outfile.write("vn")
        for coord in point[1]:
            outfile.write(" "+str(round(coord, floatnum)))
        outfile.write("\n")
        outfile.write("v")
        for coord in point[0]:
            outfile.write(" "+str(round(coord, floatnum)))
        outfile.write("\n")
    #outfile.write("# "+str(len(points))+" vertices, 0 vertices normals\n\n")
    for polygon in panels:
        outfile.write("f")
        for point in polygon:
            outfile.write(" "+str(point)+"//"+str(point))
        outfile.write("\n")
    #outfile.write("# "+str(len(panels))+" faces, 0 coords texture\n\n# End of File")
    #print(len(points), len(normvectors), len(panels), max(panels, key=lambda x: max(x)))

    outfile.close()
    return True


def export_dxf(glider, path="", midribs=0, numpoints=None, *other):
    outfile = dxf.drawing(path)
    if numpoints:
        glider.numpoints = numpoints
    other = glider.copy()
    other.mirror()
    other.cells[0].rib2 = glider.cells[0].rib1
    other.cells = other.cells[::-1] + glider.cells
    other.recalc()
    ribs = other.return_ribs(midribs)
    panels = []
    points = []
    outfile.add_layer('RIBS', color=2)
    for rib in ribs:
        outfile.add(dxf.polyface(rib*1000, layer='RIBS'))
        outfile.add(dxf.polyline(rib*1000, layer='RIBS'))
    return outfile.save()
