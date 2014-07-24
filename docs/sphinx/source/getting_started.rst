Getting Started
===============

Running Tests
-------------

To get familiar, run and take a look at the unittests.

Run all unittests (including fancy visual ones) using::

    ./testall.py -a

from the main directory.

Interactive Shell
-----------------

Openglider is intended to be used as a module in scripts.
Best practice is to use ipython notebook or normal python console::
.. code-block:: bash

    python

or
.. code-block:: bash

    ipython notebook


Next step is to create a glider, import a geometry file and modify::

    >>>glider=openglider.Glider()
    >>>glider.import_geometry("tests/demokite.ods")
    >>>for rib in glider.ribs:
    ...    rib.aoa_relative += 3
    ...
    >>>

Then, show the glider::

    >>>import openglider.graphics as graphics
    >>>polygons, points = glider.return_polygons(midribs=4)
    >>>graphics.Graphics(map(graphics.Polygon, polygons), points)

Export obj file for openfoam::

    >>>glider.export_3d('/tmp/teil.obj')

If you are not yet familiar with python, here is some places to start:

codeacademy_

`dive into python`_





.. _codeacademy: http://www.codecademy.com/de/tracks/python
.. _`dive into python`: http://www.diveintopython.net/


