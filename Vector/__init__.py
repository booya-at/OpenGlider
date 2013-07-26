import numpy as np
from Utils import *
from test.test_support import temp_cwd


def Depth(arg):
    if isinstance(arg, list) or isinstance(arg, np.ndarray):
        return max([Depth(i) for i in arg]) + 1
    else:
        return 1


def Type(arg):
    """return type of a vector list: 2d-point (1), list of 2d-points (2), 3d-point (3), list of 3d-points (4)"""
    ##2d-point//argof2d-points//3d-point//argof3d-points
    ##2d-p: depth 1
    
    ######Room for improvement here!

    if Depth(arg) == 2:
        if len(arg) == 2:
            return 1
        elif len(arg) == 3:
            return 3
        else:
            return 0
    elif Depth(arg) == 3:
        if [Depth(i) for i in arg] == [2 for i in arg]:
            if [len(i) for i in arg] == [2 for i in arg]:
                return 2
            elif [len(i) for i in arg] == [3 for i in arg]:
                return 4
            else:
                return 0
        else:
            return 0
    else:
        return 0


def Norm(vector):
    return np.sqrt(np.dot(vector, vector))


def Normalize(vector):
    return vector / Norm(vector)


def Rotation_3D(angle, axis=[1, 0, 0]):
    """3D-Rotation Matrix for (angle[rad],[axis(x,y,z)])
    see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
    a = np.cos(angle / 2)
    (b,c,d) = -Normalize(axis) * np.sin(angle / 2)
    return np.array([[a**2+b**2-c**2-d**2,  2*(b*c - a*d),          2*(b*d + a*c)],
                     [2*(b*c + a*d),        a**2+c**2-b**2-d**2,    2*(c*d - a*b)],
                     [2*(b*d-a*c),          2*(c*d + a*b),          a**2 + d**2 - b**2 - c**2]])

#def Rotation_3D_Wiki(angle,axis=[1,0,0]):

    #see http://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle for reference.
#    (x,y,z)=Normalize(axis)

class List(object):
    def __init__(self,data):
        if type(data) == 2 or type(data)==4:
            self.data=np.array(data)
    
    def __repr__(self):
        return self.data
    
    def __str__(self):
        return str(self.data)
    
    def Point(self,_ik,_k=0):
        try: (i,k)=_ik
        except: (i,k)=(_ik,_k)
        if i>len(self.data) or i < 1 or not isinstance(i, int):
            raise("invalid integer for Listpoint")
        return self.data[i-1]+k*(self.data[i]-self.data[i-1])
    
    def Extend(self,(i,k),length):
        _dir=sign(length)
        _len=abs(length)
        knew=float(0)
        
        if sign(i) is -1:
            inew=len(self.data)-i
        else:
            inew=i
        diff=0
        p2=self.Point(i,k)
        
        while diff<_len and inew<len(self.data) and inew >= 0:
            inew=inew+_dir
            p1=p2
            p2=self.data[inew]
            temp=np.linalg.norm(p2-p1)
            diff+=temp
        #we are now one further or at the end//beginning of the list
        knew=1+(_len-diff)/temp
        
        return (inew,knew)
    
    def GetLength(self,(i1,k1)=(0,0),(i2,k2)=(-2,1)):
        length=0
        if sign(i2) is -1:
            i2=len(self.data)-i2+1
        
        p1=p2=self.Point(i1,k1)
        
        while i1<i2:
            i1+=1
            p1=p2
            p2=self.data[i1]
            length+=np.linalg.norm(p2-p1)
        
        p2=self.Point(i2,k2)
        length+=np.linalg.norm(p2-p1)
        return length
        
        
        