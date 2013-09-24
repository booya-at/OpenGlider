__author__ = 'simon'

from xlrd import open_workbook

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



def import(filename):
    imp = open_workbook(filename)
    ribs = imp.sheet_by_index(0)
    cells= imp.sheet_by_index(1)

    ######import profiles

