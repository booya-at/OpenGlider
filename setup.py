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
import logging
import os
import sys
import re
import platform
import subprocess
import multiprocessing

from distutils.version import LooseVersion
from distutils.core import setup
import setuptools
from setuptools.command.build_ext import build_ext

packages, package_data = [], {}
# This is all copied 1:1 from django-project as i dont know any better way to do this
def fullsplit(splitpath, result=None):
    """
Split a pathname into components (the opposite of os.path.join)
in a platform-neutral way.
"""
    if result is None:
        result = []
    head, tail = os.path.split(splitpath)
    if head == '':
        return [tail] + result
    if head == splitpath:
        return result
    return fullsplit(head, [tail] + result)


root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
og_dirs = ['openglider', 'freecad']

for directory in og_dirs:
    for dirpath, dirnames, filenames in os.walk(directory):
        # Ignore PEP 3147 cache dirs and those whose names start with '.'
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
        parts = fullsplit(dirpath)
        package_name = '.'.join(parts)
        if '__init__.py' in filenames:
            packages.append(package_name)
        elif filenames:
            relative_path = []
            while '.'.join(parts) not in packages:
                relative_path.append(parts.pop())
            relative_path.reverse()
            if relative_path:
                path = os.path.join(*relative_path)
            else:
                path = ""
            package_files = package_data.setdefault('.'.join(parts), [])
            package_files.extend([os.path.join(path, f) for f in filenames])


package_data["openglider"] = ["py.typed"]

with open("openglider/version.py") as version_file:
    #print(version_file.read())
    version = re.match(r"__version__\s=\s['\"]([0-9\._]+)['\"]", version_file.read()).group(1)

with open("README.md") as readme_file:
    long_description = readme_file.read()

setup(
    name='OpenGlider',
    version=version,
    description="tool for glider design",
    packages=packages,
    package_data=package_data,
    license='GPL-v3',
    long_description=long_description,
    install_requires=[
        "euklid",
        "pyfoil",
        "svgwrite",
        "numpy",
        "scipy",
        "ezdxf",
        "ezodf",
        "lxml", # missing in ezodf:q;
        "pyexcel-ods",
        "meshpy",
        "cairosvg"
    ],
    author='Booya',
    url='http://openglider.org',
    download_url="https://github.com/hiaselhans/OpenGlider/tarball/0.01dev0",
    include_package_data=True
)
