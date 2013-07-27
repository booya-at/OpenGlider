import numpy ##array spec
import math
import os ##for xfoil execution
#import glob ##filename checks
import _Functions
import _XFoilCalc
import Vector


class BasicProfile2D(object):
    """Basic Profile Class, kann nicht viel, schon gar nix setzen..."""
    ####rootprof gleich mitspeichern!!
    def __init__(self, profile):
        self._SetProfile(profile)
        
    def Point(self, xval, h=-1):
        """Get Profile Point for x-value (<0:upper side) optional: height (-1:lower,1:upper), possibly mapped"""
        if isinstance(xval,(list,tuple,numpy.ndarray)):
            ##if so, treat as a common list instead...
            (i,k)=xval
            return Vector.Point(self._profile, i, k)
        else:
            return _Functions.Point(self._profile,xval,h)
        
    def Points(self, xvalues):
        """Map a list of XValues onto the Profile"""
        ####kontrollstruktur einfuegen
        ##xvalues fuer xvalues alle groesser 0 aufloesen
        ####mit point zusammenhaengen
        return numpy.array([self.Point(x) for x in xvalues])
    
    def Normalize(self):
        p1=self._profile[0]
        dmax=0.
        for i in self._profile:
            temp=Vector.Norm(i-p1)
            if temp>dmax:
                dmax=temp
                nose=i
        #to normalize do: put nose to (0,0), rotate to fit (1,0), normalize to (1,0)
        #use: a.b=|a|*|b|*cos(alpha)->
        diff=p1-nose
        sin=(diff/dmax).dot([0,-1])##equal to cross product of (x1,y1,0),(x2,y2,0)
        cos=numpy.sqrt(1-sin**2)
        matrix=numpy.array([[cos,-sin],[sin,cos]])/dmax
        self._profile=[matrix.dot(i-nose) for i in self._profile]
        
    def _SetProfile(self, profile):
        ####kontrolle: tiefe, laenge jeweils
        self._profile=numpy.array(profile)

    def _GetProfile(self):
        return self._profile
    
    Profile=property(_GetProfile, _SetProfile)

class Profile2D(BasicProfile2D):
    """2 Dimensional Standard Profile representative in OpenGlider"""
    #############Initialisation###################
    def __init__(self,profile="",name="profile"):
        ##profiltiefe->2
        ##x-y tabelle, 1tes evtl name
        ##aaa
        self.Name=name
        print(name)
        if isinstance(profile,list):
            self._SetProfile(profile)
        else:
            self._profile="nix"
        ##



    def _SetProfile(self,profile):
        ##namen filtern
        if isinstance(profile[0][0],str):
            self.Name=profile[0][0]
            i=1
        else:
            i=0

        self._rootprof=BasicProfile2D(profile[i:])
        self._rootprof.Normalize()
        self._profile=self._rootprof.Profile
        #############Initialisation end################
        
    def Import(self,pfad):
        if os.path.isfile(pfad):
            tempfile=[]
            pfile=open(pfad,"r")
            for line in pfile:
                line=line.strip()
                ###tab-seperated values except first line->name
                if "\t" in line:
                    neu=line.split("\t")
                else:
                    neu=line.split(" ")
                while "" in neu:
                    neu.remove("")
                if len(neu)==2:
                    neu=[float(i) for i in neu]
                tempfile+=[neu]
            self._SetProfile(tempfile)
            pfile.close()
        else:
            raise Exception("Profilfile gibs nicht!")

    def RootPoint(self,xval,h=-1):
        """Get Profile Point for x-value (<0:upper side) optional: height (-1:lower,1:upper); use root-profile (highest res)"""
        return self._rootprof.Point(xval, h)

    def Reset(self):
        """Reset Profile To Root-Values"""
        self.Profile=self._rootprof.Profile

    def Export(self,pfad):
        """Export Profile in .dat Format"""
        out=open(pfad,"w")
        out.write(self.Name)
        for i in self.Profile:
            #print(i)
            out.write("\n"+str(i[0])+"     "+str(i[1]))
        return pfad



    def _GetLen(self):
        return len(self._profile)

    def _GetXValues(self):
        if isinstance(self._profile,str):
            return []
        else:
            return self._profile[:,0]
    def _SetXValues(self,xval):
        """Set X-Values of profile to defined points."""
        ###standard-value: root-prof xvalues
        self.Profile=self._rootprof.Points(xval)[:,1]

    def _SetLen(self,num):
        """Set Profile to Cosinus-Distributed XValues"""
        i=num-num%2
        def xtemp(x):
            if x<1/2:
                return math.sin(math.pi*x)-1
            else:
                return 1-math.sin(math.pi*x)

        self.XValues=[xtemp(j/i) for j in range(i+1)]

    Numpoints=property(_GetLen,_SetLen)
    XValues=property(_GetXValues, _SetXValues)

class XFoil(Profile2D):
    """XFoil Calculation Profile based on Profile2D"""
    def __init__(self, profile=""):
        Profile2D.__init__(self,profile)
        self._xvalues=self.XValues
        self._calcvalues=[]
    
    def _Change(self):
        """Check if something changed in coordinates"""
        checkval=self._xvalues==self.XValues
        if not isinstance(checkval,bool):
            checkval=checkval.all()
        return checkval

    def _Calc(self,angles):

        resfile="/tmp/result.dat"
        pfile="/tmp/calc_pfile.dat"
        cfile=_XFoilCalc.Calcfile(angles,resfile)
        
        self.Export(pfile)
        status=os.system("xfoil "+pfile+" <"+cfile+" > /tmp/log.dat")
        if status==0:
            result=_XFoilCalc.Impresults(resfile)
            for i in result:
                self._calcvalues[i]=result[i]
            os.system("rm "+resfile)
        os.system("rm "+pfile+" "+cfile)
    
    def _Get(self, angle):
        if self._Change():
            self._calcvalues={}
            self._xvalues=self.XValues[:]
        print(self._calcvalues)
        calcangles=_XFoilCalc.XValues(angle, self._calcvalues)
        print("ho!"+str(calcangles))
        if len(calcangles)>0:
            erg=self._Calc(calcangles)
            print("soso")
            ##self._calcvalues=[1,2]
        return erg



#debug
#ab=Profile2D()
#ab.Import("/home/simon/Dropbox/para-lorenz/paragleiter/profile/test.dat")
#neu=ab.Point(0.1)
#print(neu)
#print(ab.Point(neu[0]))
#print("schas")
