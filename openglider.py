import Graphics as G
import Profile as P

ab=P.Profile2D()
ab.Import("/home/lo/Dropbox/production/paragleiter/profile/nichtaufgeblasen.dat")
prof=[[i[0],i[1],0.] for i in ab.Profile]
G.Graphics3D(prof,[G.Line(range(len(prof)))])