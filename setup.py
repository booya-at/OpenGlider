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
from setuptools import setup
from openglider.version import __version__

setup(
    name='OpenGlider',
    version=__version__,
    description="tool for glider design",
    packages=["openglider", "freecad.glider"],
    license='GPL-v3',
    # long_description=open('README.md').read(),
    install_requires=["svgwrite", "numpy", "scipy",
                      "ezdxf", "ezodf", "lxml",
                      "pyexcel-ods", "meshpy"],
    author='Booya',
    url='www.openglider.org',
    download_url=f"https://github.com/booya/OpenGlider/tarball/{__version__}",
    include_package_data=True
)
