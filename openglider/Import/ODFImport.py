#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.


__author__ = 'simon'
from odf.opendocument import *
import odf.table
from odf.text import P


def odfimport(filename):

    doc = load(filename)
    sheets = doc.getElementsByType(odf.table.Table)



    return sheets
# doc.save("new document.odt")


# Credits To Marco Conti for this (back in 2011)
def sheettolist(sheet):
    rows = sheet.getElementsByType(odf.table.TableRow)
    sheetlist = []
    for row in rows:
        rowarray = []
        cells = row.getElementsByType(odf.table.TableCell)
        for cell in cells:
            # repeated value?
            cellarray = ""
            repeat = cell.getAttribute("numbercolumnsrepeated")
            if not repeat:
                repeat = 1

            data = cell.getElementsByType(P)
            content = ""

            # for each text node
            for sets in data:
                for node in sets.childNodes:
                    if node.nodeType == 3:
                        content += node.data

                    for i in range(int(repeat)):  # repeated?
                        cellarray += content
            rowarray.append(cellarray)
        sheetlist.append(rowarray)

    # fill shorter lines:
    print(map(len, sheetlist))
    leng = max(map(len, sheetlist))
    for line in sheetlist:
        line += ["" for i in range(leng-len(line))]
    print(map(len, sheetlist))
    return sheetlist


