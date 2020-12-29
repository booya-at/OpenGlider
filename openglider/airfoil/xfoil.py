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


import os
import re
import asyncio
import pandas
import tempfile

import openglider.airfoil
import openglider.vector.interpolate

class XFoilCalc:
    alpha = list(range(0, 15))
    re_number = 2e6
    result = None

    file_result = "results.dat"
    ncrit = 8
    xtr_top = 0.5
    xtr_bottom = 0.5

    def __init__(self, airfoil: openglider.airfoil.Profile2D) -> None:
        super().__init__()
        self.airfoil = airfoil

    def _write_case(self, directory):
        command_file = os.path.join(directory, "xfoil_command.dat")

        alphas = "\n".join(["Alfa\n{}".format(alpha) for alpha in self.alpha])

        cmd_string = f"""
            PLOP
            g

            LOAD airfoil.dat

            CADD
            PANEL

            OPER
            VISC {self.re_number}
            VPAR
            n
            {self.ncrit}
            xtr
            {self.xtr_top}
            {self.xtr_bottom}

            PACC
            {self.file_result}
            dump.dat
            {alphas}

            quit
            """

        cmd_string = "\n".join([line.strip() for line in cmd_string.split("\n")])

        with open(command_file, "w") as outfile:
            outfile.write(cmd_string)
        
        self.airfoil.export_dat(os.path.join(directory, "airfoil.dat"))

        return command_file

    def _read_result(self, filename):
        rex_number = r"([+-]?\d+\.\d+)"
        rex_line_str = "\s+" + "\s+".join([rex_number]*9)
        rex_line = re.compile(rex_line_str)
        values = [
            "alpha",
            "ca",
            "cw",
            "cwp",
            "cm",
            "top_xtr",
            "bottom_xtr",
            "top_ltr",
            "bottom_ltr"
        ]

        data = []

        with open(filename, "r") as infile:
            for line in infile.readlines():
                match = rex_line.match(line)
                if match:
                    dct = {}
                    for name, value in zip(values, match.groups()):
                        dct[name] = float(value)
                    data.append(dct)

        df = pandas.DataFrame(data).set_index("alpha")
        df["glide"] = df["ca"]/df["cw"]
                    
        return df

    async def run(self):
        with tempfile.TemporaryDirectory() as tempdir:
            cmd_file = self._write_case(tempdir)

            proc = await asyncio.create_subprocess_shell(
                f"xfoil < {cmd_file}",
                cwd=tempdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            
            await proc.communicate()

            result_file = os.path.join(tempdir, self.file_result)
            self.result = self._read_result(result_file)
            return self.result
    
    async def run_aoa(self, aoa):
        self.aoa = [aoa - 0.1, aoa, aoa + 0.1]
        result = await self.run()
        result_dct = {}
        x=result.index.tolist()

        for column in result.columns:
            y=result[column].tolist()
            interp=openglider.vector.interpolate.Interpolation(zip(x,y))
            result_dct[column] = interp(aoa)

        return result_dct
