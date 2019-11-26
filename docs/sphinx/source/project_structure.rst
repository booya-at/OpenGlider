Project Structure
=================

OpenGlider has grown towards a set of tools:
    * airfoil: a class for easy airfoil-manipulations (map x_values, set nr. of coordinates, normalize,...)
    * freecad: freecad workbench as a possible gui
    * glider: Classes related to building paragliders:
        * Glider
        * Rib
        * Cell
        * ...
    * graphics: a wrapper to simulate mathematica-graphics with the use of vtk
    * gui: several qt-widgets
    * input: matplotlib inputs of splines, shape, aoa,...
    * jsonify: store OpenGlider objects in json format, load them and migrate between versions
    * lines: A class for LineSets which could be on paragliders, kites,...
        Line-geometry is calculated as a linear-equation-system and sag is added
    * plots: functions to create plots ready to be sent to factories
    * utils:
        * cache: a Cache-class to be inherited and a decorator to be applied on class-functions.
                    This adds a cache to calculus-intensive functions
        * bezier: a bezier curve implementation
    * vector: 2D- and 3D-vector operations and Objects (Polyline, Polygon)

Airfoil
-------

Airfoils are considered to follow the '.dat' convention, which means they
are represented by a list of (x, y) vectors, starting from upper-back via
the nose towards the lower end.
For convenience, profilepoints can be called for x-values in the range (-1,1)
whereas <0 significates a point on the upper surface, 0==nose, >0 -> lower surface


Glider
------

A glider consists of cells, which themselves consist of ribs, miniribs,..
It can also contain a LineSet
In order to create a glider you have to create ribs first, then create cells from the ribs.
Openglider defines ballooning per rib.


.. autoclass:: openglider.glider.Glider
    :members:


