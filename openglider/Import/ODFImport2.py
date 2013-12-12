__author__ = 'simon'
import ezodf
from openglider.Utils.Ballooning import BallooningBezier
from openglider.Profile import Profile2D
from openglider.Ribs import Rib
import numpy


def import_ods(filename):
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets
    profiles = [Profile2D(profile) for profile in transpose_columns(sheets[3])]
    # Ballooning old : 1-8 > upper (prepend/append (0,0),(1,0)), 9-16 > lower (same + * (1,-1))
    balloonings_temp = transpose_columns(sheets[4])
    balloonings = []
    for baloon in balloonings_temp:
        upper = [[0, 0]] + baloon[:7] + [[1, 0]]
        lower = [[0, 0]] + [[i[0], -1*i[1]] for i in baloon[8:15]] + [[1, 0]]
        balloonings.append(BallooningBezier([upper, lower]))


    ribs = []
    main = sheets[0]
    main = ezodf.Table()
    point = numpy.array([0, 0, 0])
    alpha2 = span_last = 0.
    # Glide -> DATAIMPORT
    for i in range(1, main.nrows()):
        line = [main.get_cell(i, j).value for j in main.ncols()]
        chord = line[1]
        span = line[2]
        point[0] = line[3]
        alpha1 = alpha2
        alpha2 += line[4]*numpy.pi/180
        alpha = (span > 0)*(alpha1+alpha2)*0.5 + line[6]
        point[2] -= (i > 1) * numpy.sin(alpha1) * (line[2] - span_last)  # i>1 redundant, because alpha1=0
        # AOA = line[5]
        # zrot -> line[7]
        # Profmerge -> line[8]
        # balmerge -> line[9]

        span_last = line[2]






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




    return profiles


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