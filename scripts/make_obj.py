#!/bin/python2
import sys
import os
import math
import numpy as np
import euklid
from openglider.glider import Glider

if len(sys.argv) >= 4:
    inputfile = os.path.abspath(sys.argv[1])
    destfile = os.path.dirname(inputfile) + "/geometry.obj"
    glider = Glider.import_geometry(inputfile)
    for cell in glider.cells:
        pass
        #cell.miniribs.append(openglider.Ribs.MiniRib(0.5, 0.7))

    numpoints = int(sys.argv[3])
    if numpoints == 0:
        numpoints = None
    else:
        glider.profile_numpoints = numpoints
    print("numpoints: ", numpoints)
    midribs = int(sys.argv[2])
    print("midribs: ", midribs)

    glider.export_3d(destfile, midribs=midribs, numpoints=numpoints)

    # Print v_inf, ca_projection, cw_projection
    alpha = math.atan(1 / glider.ribs[0].glide)
    v = glider.data["GESCHWINDIGKEIT"]
    v_inf = euklid.vector.Vector3D([-math.cos(alpha) * v, 0, -math.sin(alpha) * v])
    ca = euklid.vector.Vector3D([-v_inf[2], 0, v_inf[0]]).normalized()
    print("v_inf ", v_inf)
    print("ca: ", ca)
    print("cw: ", v_inf.normalized())
else:
    print("please give me an input file + number of midribs + numpoints (0=Original)")
