Getting Started
===============

Running Tests
-------------

To get familiar, run and take a look at the unittests.

Run all unittests (including fancy visual ones) using::

    ./testall -a

from the main directory.

Interactive Shell
-----------------

Best practice is to use python as a module.
to do so launch a python console::

    python2
    >>> import openglider

if you have ipython installed, you can also run a graphical window, save input, reload,..::

    ipython2 qtconsole
    In [1]: import openglider

Next step is to create a glider, import a geometry file and modify::

    >>>glider=openglider.Glider()
    >>>glider.import_geometry("tests/demokite.ods")
    >>>for rib in glider.ribs:
    ...    rib.aoa_relative += 3
    ...
    >>>

Then, guess what, show the glider::

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


