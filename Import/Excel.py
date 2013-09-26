__author__ = 'simon'

from xlrd import open_workbook
from Profile import Profile2D

def Import(filename):
    imp = open_workbook(filename)
    ribs = sheettolist(imp.sheet_by_index(0)) ### cellnr/chord/xval/yval/arcangle/aoa/z-rot/arcrot-offset/merge/baloon
    cells= sheettolist(imp.sheet_by_index(1))

    ######import profiles
    profiles=profileimp(imp.sheet_by_index(3))

    for i in range(1,len(ribs)):




    return ribs

def sheettolist(sheet):
    thadict=[i.value for i in sheet.row(0)]

    return [[sheet.cell(j,i).value for i in range(len(thadict))] for j in range(sheet.nrows)]


def profileimp(sheet):
    num=sheet.row_len(1)/2
    profiles=[]

    for i in range(num):
        prof=Profile2D()
        j=0

        if isinstance(sheet.cell(0,2*i).value,str):
            prof.Name=sheet.cell(0,2*i).value
            j=j+1
        temp=[]
        while j<sheet.nrows and isinstance(sheet.cell(j,2*i).value,float):
            #print(sheet.cell(j,2*i).value)
            temp+=[[sheet.cell(j,2*i).value,sheet.cell(j,2*i+1).value]]
            j=j+1
        prof.Profile=temp

        profiles+=[prof]
    return profiles


