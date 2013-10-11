from Vector import rotation_3d

###########entweder klasse oder funktion die funktion erzeugt


def rotation(aoa, arc, zrot):
    ##rotation-matrix
    ##aoa:
    rot=rotation_3d(aoa,[0,0,1])
    ##arc-wide rotation matrix
    rot=rot.dot(rotation_3d(arc,[1,0,0]))
    ##rotation relative to profile z-axis
    axis=rot.dot([0,1,0])
    
    return rot.dot(rotation_3d(zrot,axis))