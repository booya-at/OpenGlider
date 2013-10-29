from openglider.Vector import rotation_3d
import math
###########entweder klasse oder funktion die funktion erzeugt


def rotation(aoa, arc, zrot):
    ##rotation-matrix
    ##aoa:
    print((aoa,arc,zrot))
    rot=rotation_3d(arc+math.pi/2,[-1,0,0])
    #arc-wide rotation matrix
    axis=rot.dot([0,0,1])
    rot=rotation_3d(aoa*math.pi/180,axis).dot(rot)
    #rotation relative to profile z-axis
    axis=rot.dot([0,1,0])
    rot=rotation_3d(zrot*math.pi/180,axis).dot(rot)
    rot=rotation_3d(-math.pi/2,[0,0,1]).dot(rot)
    
    return rot