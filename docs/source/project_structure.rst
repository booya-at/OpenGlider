Project Structure
=================

OpenGlider is organised as a set of Python packages:

* **openglider** — main library (see :doc:`api/index` for full API).
* **freecad.glider** — FreeCAD workbench (see :doc:`freecad_workbench`).

Main ``openglider`` subpackages
-------------------------------

* **airfoil** — 2D/3D airfoil handling: normalise, resample, conformal mapping,
  parametric profiles. Profiles follow the ``.dat`` convention (see
  :doc:`concepts`).

* **glider** — Core glider data:
  * **Glider**, **Cell**, **Rib** (and miniribs), ballooning, shape.
  * **ParametricGlider** — 2D/parametric design (ODS import/export, shape, arc).
  * **in_out** — import/export 3D geometry and spreadsheet data.

* **lines** — **LineSet**, lines, and nodes. Line geometry is computed as a
  linear system; sag can be added. Used for paragliders, kites, etc.

* **mesh** — Triangulated 3D mesh from a Glider (and optional lines). Export to
  OBJ, DXF, etc.

* **plots** — Cutting patterns, DXF export, spreadsheets (material lists,
  straps, rigidfoils), and sketches (line plan, shape plot).

* **vector** — 2D/3D vector maths, polylines, polygons, splines (Bezier, B-spline),
  projection, drawing layout.

* **graphics** — VTK-based visualisation (polygons, points) for quick 3D
  inspection.

* **jsonify** — Serialise/deserialise OpenGlider objects to JSON and migrate
  between schema versions.

* **utils** — Helpers: cache (cached properties), distribution, colors, table,
  etc.

Glider and Airfoil (short reference)
------------------------------------

A **Glider** is made of **Cells**; each cell is defined by two **Ribs** (and
optional miniribs). Ballooning is defined per rib. The **LineSet** attaches
to the canopy. See :doc:`concepts`.

**Airfoils** are lists of (x, y) points from upper trailing edge via nose to
lower trailing edge. You can query points by normalised x in (-1, 1). See
:doc:`concepts`.

API reference
------------

For detailed class and function documentation, see the :doc:`api/index`.
