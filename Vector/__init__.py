import numpy as np
from Utils import *


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

def Point(data,i,k):
    if i>len(data) or i < 0 or not isinstance(i, int):
        print("invalid integer for Listpoint")
    return data[i]+k*(data[i+1]-data[i])


class List(object):
    def __init__(self,data=""):
        if Type(data) == 2 or Type(data)==4:
            self.data=np.array(data)
        
    def __repr__(self):
        return self.data
    
    def __str__(self):
        return str(self.data)
    
    def Point(self,_ik,_k=0):
        try: (i,k)=_ik
        except: (i,k)=(_ik,_k)
        return Point(self.data, i, k)
    
    def Extend(self,(i,k),length):
        """Extend the List at a given Point (i,k) by the given Length and return NEW (i,k)"""
        _dir=sign(length)
        _len=abs(length)
        
        p1=self.Point(i,k)
        
        if _dir==1:
            (inew,knew)=(i+1,0)
        else:
            (inew,knew)=(i,0)
        p2=self.data[inew]
        diff=np.linalg.norm(p2-p1)
        while diff<_len and inew<len(self.data)-1 and inew > 0:
            inew=inew+_dir
            p1=p2
            p2=self.data[inew]
            temp=np.linalg.norm(p2-p1)
            diff+=temp
        #we are now one too far or at the end//beginning of the list
       
        inew-=(_dir+1)/2 ##only for positive direction
        if inew==i:##New Point is in the same 'cell'
            d1=np.linalg.norm(p1-self.data[i])
            knew=k/d1*(d1+length)
        else:
            knew=(diff-_len)/temp##
            if _dir==1: knew=1-knew
       
        return (inew,knew)
    
    def GetLength(self,(i1,k1)=(0,0),(i2,k2)=(-2,1)):
        length=0
        if sign(i2) is -1:
            i2=len(self.data)+i2
        #print(i2)
        
        p1=self.Point(i1,k1)
        p2=p1
        
        while i1<i2:
            i1+=1
            p1=p2
            p2=self.data[i1]
            length+=np.linalg.norm(p2-p1)
        
        p2=self.Point(i2,k2)
        length+=np.linalg.norm(p2-p1)
        return length

"""       
####debug sec
cd=List([[0,0],[1,0],[2,0]])
neu=[cd.Extend((1, 0.5), i) for i in [-3.2,-1,-0.2,0,0.2,1,3]]##all possible cases to be tested
abc=cd.GetLength()
<<<<<<< HEAD
#print(abc)
=======
neu2=[cd.Point(i) for i in neu]
print(abc)
>>>>>>> master
####
      """  
