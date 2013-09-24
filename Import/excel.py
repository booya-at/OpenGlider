__author__ = 'simon'

from xlrd import open_workbook
from Profile import Profile2D

"""
a=xlrd.open_workbook(filename)
a.nsheets

a.sheet_by_index(index)
    .nrows -> numlines
    .row_len(i) -> columns
    .row(i)
        [j].value

a.cell(i,j)
    .value
"""



def Import(filename):
    imp = open_workbook(filename)
    ribs = imp.sheet_by_index(0)
    cells= imp.sheet_by_index(1)

    ######import profiles
    profiles=profileimp(imp.sheet_by_index(4))

    return profiles





def profileimp(sheet):
    num=sheet.row_len(1)/2
    profiles=[]

    for i in range(num):
        prof=Profile2D()
        j=0

        if isinstance(sheet.cell(0,2*i).value,str):
            prof.Name=sheet.cell(0,2*i).value
            j=j+1
        while isinstance(sheet.cell(j,2*i),float):
            prof.Profile+=[sheet.cell(j,2*i),sheet.cell(j,2*i+1)]

        profiles+=[prof]
    return profiles


