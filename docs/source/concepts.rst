Concepts
========

This section explains the main concepts and data structures used in OpenGlider.

Glider hierarchy
----------------

A **Glider** is the top-level 3D representation of a paraglider or kite. It
consists of:

* **Cells** — each cell is the volume between two ribs (and optional miniribs).
* **Ribs** — define the wing profile at a given span position; each rib has an
  airfoil, twist (angle of attack), and position.
* **LineSet** — lines and attachment points (nodes) that connect the canopy to
  the harness.

Structure::

   Glider
   ├── Cells (list of Cell)
   │   ├── rib1, rib2 (Rib)
   │   ├── miniribs (optional)
   │   ├── panels, diagonals, straps
   │   └── ...
   └── LineSet
       ├── lines (Line)
       └── attachment points (nodes)

To build a glider you typically create ribs first, then cells from adjacent
ribs, then attach a LineSet.

Coordinate system
-----------------

* **x** — longitudinal (positive = forward / nose).
* **y** — span (positive = right wing).
* **z** — vertical (positive = up).

Airfoil / profile coordinates
-----------------------------

Profiles follow the common ``.dat`` convention: a list of (x, y) points from
trailing edge (upper) via nose to trailing edge (lower). For convenience,
profile points can be queried by a normalised x in **(-1, 1)**:

* **x < 0** — upper surface
* **x = 0** — nose
* **x > 0** — lower surface

Ballooning
----------

Ballooning (excess fabric between ribs) is defined **per rib** in OpenGlider.
It affects the 3D shape of the canopy between ribs.

Parametric vs 3D glider
-----------------------

* **ParametricGlider** — 2D/parametric representation (shape, arc, profile
  distribution, spreadsheet-style). Used for design and import from ODS.
* **Glider** — 3D geometry built from cells and ribs. Used for mesh export,
  lines, and visualisation.

You can convert from parametric to 3D with ``ParametricGlider.get_glider_3d()``.

Lines and LineSet
-----------------

The **LineSet** holds all lines and their attachment points. Line geometry is
solved as a linear system; sag can be added. Attachment points reference ribs
or cells.

Mesh
----

A **Mesh** is a triangulated 3D surface (and optionally lines) generated from
a Glider. It can be exported to OBJ (e.g. for CFD or FreeCAD) or other formats.

Plots and patterns
------------------

The **plots** subpackage provides functions to generate cutting patterns,
DXF exports, and factory-ready drawings from a glider project.
