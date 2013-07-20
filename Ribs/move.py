import math
import numpy as np
from ..Vector import Rotation_3D


###########entweder klasse oder funktion die funktion erzeugt


def mapfunc():


def rotation(aoa, arc, zrot):
    ##aoa-rotation-matrix
    """

    :param aoa:
    :param arc:
    :param zrot:
    :return:
    """
    rot_aoa = lambda x: (math.cos(aoa) * x[0] - math.sin(aoa) * x[1], math.sin(aoa) * x[0] + math.cos(aoa) * x[1])

    ##arc-wide rotation matrix
    rot_arc = ((math.cos(arc), 0, math.sin(arc)), (0, 1, 0), (-math.sin(arc), 0, math.cos(arc)))

    rot_zrot = 9

    return lambda x: rot_zrot.dot(rot_arc.dot(rot_aoa(x)))