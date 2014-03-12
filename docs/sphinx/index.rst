========================
OpenGlider Documentation
========================

Getting Started
===============

Installation
------------

install all dependencies first:
    * ezodf2
    * dxfwrite
    * scipy
    * (svgwrite)
    * (vtk)

clone the repo::

    git clone https://github.com/hiaselhans/OpenGlider.git


install using setup.py::

    python2 setup.py install


(developers choice)::

    python2 setup.py develop


Running Tests
-------------

To get familiar, take a look at the unittests.

Run all unittests (including fancy visual ones) using::

    ./testall -a

from the main directory.


Project Structure
=================

All glider specific classes are in 'openglider/glider/'



Developer
=========

There is a lot to do, including:
    * Creating good code
    * Writing documentation
    * Run and write unittests

Code Conventions
----------------

Code conventions are pretty redundant for python, but:
    * Use python-3 compatible Language::

        print("use print as a function")

    * Best practice: http://www.python.org/dev/peps/pep-0008/
    * Write unittests for everything

Class Reference
===============

.. toctree::

    source/modules.rst



