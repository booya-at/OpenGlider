__author__ = 'simon'

from xlrd import open_workbook
from openglider.Profile import Profile2D
from openglider.Ribs import Rib
from openglider.Graphics import Graphics, Line


def excelimport(filename):
    imp = open_workbook(filename)
    ribsheet = sheettolist(
        imp.sheet_by_index(0)) ### cellnr/chord/xval/yval/arcangle/aoa/z-rot/arcrot-offset/merge/baloon
    cellsheet = sheettolist(imp.sheet_by_index(1))

    ######import profiles
    profiles = profileimp(imp.sheet_by_index(3))
    xvalues = profiles[0].XValues
    for profil in profiles:
        profil.XValues = xvalues

    ######import ballooning



    def merge(factor):
        num = int(factor)
        val = factor - num
        if val > 0 and num < len(profiles):
            prof = profiles[num] * (1 - val) + profiles[num + 1] * val
        else:
            prof = profiles[num]
        return prof

    rippen = []
    arcang = 0.
    front = [0., 0., 0.]
    for i in range(1, len(ribsheet)):
        # row: num, chord, x, y, angle, aoa, z-rot, angle-offset, merge, balloonmerge
        # Profile:
        profil = merge(ribsheet[i, 8])


        # Ballooning


        # Rib


        # Cell

        #rippen.append(Rib(profil,front,arcang,ribsheet[i,5],zrot,glide,"Rib_"+str(i)))
        # Mittelzelle -> rib.mirror, append mirrorrib, rib
        print("jo hier kommt die Aufbauarbeit")
        """
        old mathematica code:
        	aoaabs={};
            alpha2=0;
            z=0;
            x=0;
            {
            Table[
                spw=excel[[i,3]];
                y=excel[[i,4]];
                chord=excel[[i,2]];
                alpha1=alpha2;
                alpha2+=excel[[i,5]]*Pi/180;
                If[x==0,alpha=0,alpha=(alpha1+alpha2)/2];
                If[i>1,z=z-Sin[alpha1]*(spw-excel[[i-1,3]])];
                x=x+Cos[alpha1]*(spw-If[i>1,excel[[i-1,3]],0]);

                beta=ArcTan[Cos[alpha]/gleitzahl]-excel[[i,6]]*Pi/180;(*Anstellwinkel*)
                AppendTo[aoaabs,{spw,-beta*180/Pi}];
                gamma=ArcTan[Sin[alpha]/gleitzahl]*excel[[i,7]];(*faktor 0-1; winkel um profilz-achse*)
                rot1=RotationMatrix[alpha+excel[[i,8]]/180.*Pi,{0,1,0}];(*um profilxachse, +offset*)
                rot2=RotationMatrix[beta,rot1.{1,0,0}].rot1;
                rot3=RotationMatrix[gamma,rot2.{0,0,1}].rot2;
                rot=chord*rot3;
                trans={x,y,z};
                {trans,rot},{i,Length[excel]}]
        """
        ab = Rib()

        ab.profile_2d = merge(ribsheet[i, 8])
        ab.AOA = [ribsheet[i, 6], False]
        #ab.arcang=
        ab.name = "rib" + str(i + 1)
        #ab.glide
        #ab.zrot
        #ab.pos
        #ab.ReCalc()

        rippen.append(ab)
        ###bp=int(fak) fak=fak-int(fak)
        ###if fak>0 -> bneu=b[bp]*(1-fak)+bneu[bp+1]*fak else b[bp]
        ###

        Graphics[[Line(i.profile3D) for i in rippen]]

    return rippen


def sheettolist(sheet):
    thadict = [i.value for i in sheet.row(0)]
    return [[sheet.cell(j, i).value for i in range(len(thadict))] for j in range(sheet.nrows)]


def profileimp(sheet):
    num = sheet.row_len(1) / 2
    profiles = []

    for i in range(num):
        prof = Profile2D()
        j = 0

        if isinstance(sheet.cell(0, 2 * i).value, str):
            prof.name = sheet.cell(0, 2 * i).value
            j += 1
        temp = []
        while j < sheet.nrows and isinstance(sheet.cell(j, 2 * i).value, float):
            #print(sheet.cell(j,2*i).value)
            temp += [[sheet.cell(j, 2 * i).value, sheet.cell(j, 2 * i + 1).value]]
            j += 1
        prof.Profile = temp

        profiles += [prof]
    return profiles


