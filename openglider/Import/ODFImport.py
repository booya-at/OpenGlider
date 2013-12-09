__author__ = 'simon'
from odf.opendocument import load
import odf.table as ods
from odf.text import P as odText

def OdfImport(filename):

    doc = load("my document.odt")
    sheets = doc.getElementsByType(ods.Table)




# doc.save("new document.odt")



# Credits To Marco Conti for this (back in 2011)
def sheettolist(sheet):
    rows = sheet.getElementsByType(ods.TableRow)
    rowarray = []
    for row in rows:
        cellarray = []
        cells = row.getElementsByType(ods.TableCell)
        for cell in cells:
            # repeated value?
            repeat = cell.getAttribute("numbercolumnsrepeated")
            if not repeat:
                repeat = 1

            data = cell.getElementsByType(odText)
            content = ""

            # for each text node
            for sets in data:
                for node in sets.childNodes:
                    if node.nodeType == 3:
                        content += unicode(node.data)

                    for i in range(int(repeat)):  # repeated?
                        cellarray.append(content)
            rowarray.append(cellarray)
    return rowarray


