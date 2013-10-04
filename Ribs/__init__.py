from move import rotation#, alignment
from Profile import Profile2D, Profile3D
import numpy
from Vector import Type


class Rib(object):
    """Openglider Rib Class: contains a profile, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition"""

    def __init__(self, profile="", startpoint=numpy.array([0, 0, 0]), arcang="", aoa="", zrot="", glide="", name="unnamed rib",aoaabs=False,startpos=0.):
        self.name = name
        if isinstance(profile, list):
            self.profile_2d = Profile2D(profile, name=name)
        self._aoa=(aoa,aoaabs)
        self.aoa=[0,0]
        self.glide=glide
        self.arcang=arcang
        self.zrot=zrot
        self.pos=startpoint
        
        #self.ReCalc()


    def Align(self, points):
        ptype=Type(points)
        if ptype==1:
            return self.pos+self._rot.dot([points[0],points[1],0])
        if ptype==2 or ptype==4:
            return [self.Align(i) for i in points]
        if ptype==3:
            return self._rot.dot(points)
    
    def _SetAOA(self,aoa):
        try:
            self._aoa=(aoa[0],bool(aoa[1]))
        except:
            self._aoa=(float(aoa),False)#default: relative aoa
    def _GetAOA(self):
        return dict(zip(["rel","abs"],self.aoa))###return in form: ("rel":aoarel,"abs":aoa)
    
    
    def ReCalc(self):
        ##recalc aoa_abs/rel
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        diff=numpy.arctan(numpy.cos(self.arcang)/self.glide)
        ##aoa->(rel,abs)
        #########checkdas!!!!!
        self.aoa[self._aoa[1]]=self._aoa[0]
        self.aoa[1-self._aoa[1]]=diff+self._aoa[0]
        
        self._rot=rotation(self.aoa[1],self.arcang, self.zrot)
        self.profile3D=Profile3D(self.Align(self.profile_2d.Profile))

    def mirror(self):
        self.arcang=-self.arcang
        self.zrot=-self.zrot
        self.pos=-self.pos
        self.ReCalc()

    def copy(self):
        return self.__class__(self.profile_2d.copy(),self.pos,self.arcang,self.aoa,self.zrot,self.glide,self.name+"_copy",self.aoa[1])
        
    AOA=property(_GetAOA,_SetAOA)
        
