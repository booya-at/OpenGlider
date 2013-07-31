<<<<<<< HEAD
import Graphics as G
import Profile as P

ab=P.Profile2D()
ab.Import("/home/lo/Dropbox/production/paragleiter/profile/nichtaufgeblasen.dat")
prof=[[i[0],i[1],0.] for i in ab.Profile]
G.Graphics3D(prof,[G.Line(range(len(prof)))])
=======
import Profile
#import Vector
import Ribs
import Graphics

##simon debug
p1=Profile.Profile2D()
p1.Import("/home/simon/Dropbox/para-lorenz/paragleiter/profile/nichtaufgeblasen.dat")

rib=Ribs.rib(profile=p1,glide=7)
rib.AOA=4*3.141/180
rib.arcang=20*3.141/180
rib.zrot=0
print(rib.AOA)
rib.ReCalc()



#from .Ribs import Rib
##import .Profile

####Nothing here yet :(
"""
import Graphics as G
gobj = G.Line([[0,0,1],[0,0,2]])
print(gobj.coordinates)
gobj._SetColour('green')
print(gobj.colour)
>>>>>>> lo:__init__.py
"""

>>>>>>> master
