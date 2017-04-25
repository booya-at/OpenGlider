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
    ```python
    straps = []
    straps.append({left_front:0.1, left_back:0.2, right_front:0.1, right_back:0.2, material_code="", name="unnamed"})
    ```
    * holes
    * rigidfoils
    ```python
    rf = []
    rf.append({"start":-0.2, "end":0.09, "distance":0.005, "ribs":[0, 1, 2, 3, 4})
    par_glider.elements["rigid_foils"] = rf
    
    ```
