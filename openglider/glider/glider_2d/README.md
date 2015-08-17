Parametric Glider
=================


This contains a parametric (flat) representation of a glider.

it consists of several spline curves:

* front
* back
* arc-line
* angle-of-attack curve
* ballooning interpolation curve
* airfoil interpolation curve
* rib_no->x-value curve

Further it has the following properties:

* a list of airfoils to interpolate
* a list of balloonings to interpolate
* cell_no
* speed
* glide
* elements
    * diagonals
    * straps
    * holes
    * ...