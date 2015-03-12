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


import tempfile
#import os

def XValues(list1, list2):
    """Get a list of Values to compare against another one and delete values if not necessary to calculate again"""
    ###check for list1 to be a list of angles
    if isinstance(list1, list):
        temp = list1[:]
    else:
        temp = [list1]
    temp2 = temp[:]
    ###check if list2 is not empty and remove all values already calculated from temp2
    if len(list2) > 0:
        print(temp)
        for i in temp:
            if i in list2[:][0]:
                temp2.remove(i)
    return temp2


def Calcfile(aoalist, xfoutput=tempfile.gettempprefix() + '/xfoutput.dat', renum=200000):
    """Export Calculation command file"""
    temporarydict = tempfile.gettempprefix()
    print(temporarydict)
    cfile = '/' + temporarydict + '/xfoilcommand.dat'

    alphas = ["ALFA\n{}".format(alpha) for alpha in aoalist]

    string = """
    LOAD {airfoil}

    CADD
    PANEL

    OPER
    VISC {re_number}
    PACC
    {polar_file}
    {dump_file}

    {alphas}

    quit
    """

    return string.format(re_number=renum, polar_file=cfile, dump_file="", alphas=alphas)

    # xfcommand = open(cfile, 'w')
    #
    # xfcommand.write('plop\ng\n\n')
    # ##define Re-Num
    # xfcommand.write('OPER\nRE\n' + str(renum) + '\n')
    # xfcommand.write('VISC\n')
    # xfcommand.write('PACC\n' + xfoutput + '\n' + xfoutput + '2.dat\n')
    # if isinstance(aoalist, list):
    #     for aoa in aoalist:
    #         xfcommand.write('ALFA\n')
    #         xfcommand.write(str(aoa) + '\n')
    # else:
    #     xfcommand.write('ALFA\n')
    #     xfcommand.write(str(aoalist) + '\n')
    # xfcommand.write('\nquit')
    # xfcommand.close()
    # return cfile


def Impresults(resfile):
    xfile = open(resfile, "r")
    init = 0
    erg = {}
    index = temp = []  # due to pydev-error

    for line in xfile:
        line = line.strip()
        if len(line) > 0:
            line = line.split(" ")
            ##remove leading zero-elements
            while "" in line:
                line.remove("")
            print(line)
            if init == 1:
                erg[float(line[0])] = {index[i]: float(line[i]) for i in range(1, len(line))}
            if line[0][0] == "-":
                print("ok")
                init = 1
                index = temp
            temp = line
    print(index)
    return erg


def calculate_airfoil(airf, aoas):
    with tempfile.NamedTemporaryFile(suffix=".dat") as outfile:
        airf.export_dat("/tmp/airfoil.dat")
        outfile.write(Calcfile(aoas))

