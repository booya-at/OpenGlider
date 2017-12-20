#!/bin/python2
import sys
import os
import math
import numpy as np
from openglider.glider import Glider
from openglider.vector.functions import normalize

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
    v_inf = [-math.cos(alpha) * v, 0, -math.sin(alpha) * v]
    ca = normalize([-v_inf[2], 0, v_inf[0]])
    print("v_inf ", v_inf)
    print("ca: ", ca)
    print("cw: ", normalize(v_inf))
else:
    print("please give me an input file + number of midribs + numpoints (0=Original)")
