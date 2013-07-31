from Vector import Rotation_3D

###########entweder klasse oder funktion die funktion erzeugt


def rotation(aoa, arc, zrot):
    ##rotation-matrix
    ##aoa:
    rot=Rotation_3D(aoa,[0,0,1])
    ##arc-wide rotation matrix
    rot=rot.dot(Rotation_3D(arc,[1,0,0]))
    ##rotation relative to profile z-axis
    axis=rot.dot([0,1,0])
    
    return rot.dot(Rotation_3D(zrot,axis))