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


class CMakeExtension(setuptools.Extension):
    def __init__(self, name, sourcedir=''):
        super().__init__(name, [])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        
        num_cores = multiprocessing.cpu_count()

        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', f'-j{num_cores}']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        logging.info(f"Build dir: {self.build_temp}")
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)


setup(
    name='OpenGlider',
    version="0.05",  #openglider.__version__,
    description="tool for glider design",
    packages=packages,
    package_data=package_data,
    ext_modules=[CMakeExtension('.')],
    cmdclass={"build_ext": CMakeBuild},
    license='GPL-v3',
    # long_description=open('README.md').read(),
    install_requires=["svgwrite",
                    "numpy",
                    "scipy",
                    "ezdxf",
                    "ezodf",
                    "lxml", # missing in ezodf:q;
                    "pyexcel-ods",
                    "meshpy"
                    ],
    author='Booya',
    url='www.openglider.org',
    download_url="https://github.com/hiaselhans/OpenGlider/tarball/0.01dev0",
    include_package_data=True
)
