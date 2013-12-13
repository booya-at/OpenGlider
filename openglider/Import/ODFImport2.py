__author__ = 'simon'
import ezodf
from openglider.Utils.Ballooning import BallooningBezier
from openglider.Profile import Profile2D
from openglider.Ribs import Rib
from openglider.Cells import Cell
#from openglider.glider import Glider
import numpy


def import_ods(filename, glider=None):
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets
    # Profiles -> map xvalues
    profiles = [Profile2D(profile) for profile in transpose_columns(sheets[3])]
    xvalues = sorted(profiles, key=lambda prof: prof.Numpoints)
    # Ballooning old : 1-8 > upper (prepend/append (0,0),(1,0)), 9-16 > lower (same + * (1,-1))
    balloonings_temp = transpose_columns(sheets[4])
    balloonings = []
    for baloon in balloonings_temp:
        upper = [[0, 0]] + baloon[:7] + [[1, 0]]
        lower = [[0, 0]] + [[i[0], -1*i[1]] for i in baloon[8:15]] + [[1, 0]]
        balloonings.append(BallooningBezier([upper, lower]))

    ribs = []
    cells = []
    main = sheets[0]
    point = numpy.array([0., 0., 0.])
    alpha2 = span_last = 0.
    # Glide -> DATAIMPORT
    for i in range(1, main.nrows()):
        line = [main.get_cell([i, j]).value for j in range(main.ncols())]
        if not line[0]:
            print("leere zeile:", i, main.nrows())
            break
        print(line)
        chord = line[1]
        span = line[2]  # spanwise
        point[0] = line[3]  # x-value -> front/back (ribwise)
        alpha1 = alpha2  #angle before the rib
        alpha2 += line[4]*numpy.pi/180  # angle after the rib (given in degrees)
        alpha = (span > 0)*(alpha1+alpha2)*0.5 + line[6] * numpy.pi/180  # rib's angle
        point[1] += numpy.cos(alpha1) * (span - span_last)  # y-value -> spanwise
        point[2] -= numpy.sin(alpha1) * (span - span_last)  # z-axis -> up/down
        aoa = line[5] * numpy.pi/180
        zrot = line[7] * numpy.pi/180
        span_last = span

        # Merge Profiles/balloonings
        def merge(factor, container):
            k = factor % 1
            i = int(factor - k)
            first = container[i]
            if k > 0:
                second = container[i+1]
                return first * (1-k) + second * k
            return first
        profile = merge(line[8], profiles)
        if i == main.nrows() - 3:
            profile = profile * 0.0001
        ballooning = merge(line[9], balloonings)
        print(point)

        ribs.append(Rib(profile, ballooning, point, chord, alpha, aoa, zrot))
        ribs[-1].recalc()
        if i == 1 and point[1] is not 0:
            # MIDRIB
            rib = ribs[0].copy()
            rib.mirror()
            rib.recalc()
            ribs = [rib, ribs[0]]
        if len(ribs) > 1:
            cells.append(Cell(ribs[-2], ribs[-1], []))
            cells[-1].recalc()

    cells[-1].rib2.profile_2d *= 0.01
    cells[-1].rib2.recalc()
    cells[-1].recalc()
    if glider:
        glider.cells = cells
    return cells

            #old mathematica code:
            #aoaabs={};
            #alpha2=0;
            #z=0;
            #x=0;
            #{
            #Table[
            #    spw=excel[[i,3]];
            #    y=excel[[i,4]];
            #    chord=excel[[i,2]];
            #    alpha1=alpha2;
            #    alpha2+=excel[[i,5]]*Pi/180;
            #    If[x==0,alpha=0,alpha=(alpha1+alpha2)/2];
            #    If[i>1,z=z-Sin[alpha1]*(spw-excel[[i-1,3]])];
            #    x=x+Cos[alpha1]*(spw-If[i>1,excel[[i-1,3]],0]);
            #
            #    beta=ArcTan[Cos[alpha]/gleitzahl]-excel[[i,6]]*Pi/180;(*Anstellwinkel*)
            #    AppendTo[aoaabs,{spw,-beta*180/Pi}];
            #    gamma=ArcTan[Sin[alpha]/gleitzahl]*excel[[i,7]];(*faktor 0-1; winkel um profilz-achse*)
            #    rot1=RotationMatrix[alpha+excel[[i,8]]/180.*Pi,{0,1,0}];(*um profilxachse, +offset*)
            #    rot2=RotationMatrix[beta,rot1.{1,0,0}].rot1;
            #    rot3=RotationMatrix[gamma,rot2.{0,0,1}].rot2;
            #    rot=chord*rot3;
            #    trans={x,y,z};
            #    {trans,rot},{i,Length[excel]}]


def transpose_columns(sheet=ezodf.Table(), columnswidth=2):
    num = sheet.ncols()
    #if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(num/columnswidth):
        columns = range(col*columnswidth, (col+1)*columnswidth)
        element = []
        i = 0
        while i < sheet.nrows():
            row = [sheet.get_cell([i, j]).value for j in columns]
            if sum([j is None for j in row]) == len(row):  # Break at empty line
                break
            i += 1
            element.append(row)
        result.append(element)
    return result