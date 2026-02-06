FreeCAD Workbench
=================

OpenGlider provides a **FreeCAD workbench** for interactive paraglider design
inside FreeCAD. The workbench is in the ``freecad/glider`` package and is
loaded when FreeCAD starts with OpenGlider installed.

Overview
-------

* **Name:** Glider workbench
* **Purpose:** Paraglider/kite design: shape, arc, ribs, ballooning, cells,
  lines, cuts, and export of patterns/panels.

The workbench uses the same ``openglider`` Python library for geometry; FreeCAD
is the GUI and document host.

Main tools (examples)
---------------------

* **Create/Import glider** — create a new parametric glider or import from file.
* **Shape / Arc / AOA / Airfoil / Ballooning** — edit 2D design parameters.
* **Cell / Line** — edit cells and line sets.
* **Pattern / Panel / Import DXF** — production and import.
* **View** — visualisation of the glider.

Installation for FreeCAD
------------------------

1. Install FreeCAD (e.g. from your system package manager or `FreeCAD
   <https://www.freecadweb.org/>`_).
2. Install OpenGlider so that Python can import both ``openglider`` and the
   FreeCAD modules (e.g. ``pip install -e .`` from the OpenGlider repo).
3. Install a custom **pivy** build for your FreeCAD version if needed; see
   `looooo/pivy <https://github.com/looooo/pivy>`_.
4. Start FreeCAD; the Glider workbench should appear in the workbench list.

Using with pixi
---------------

From the OpenGlider project root::

   pixi run freecad

This starts FreeCAD with the correct environment and OpenGlider available.

Further resources
-----------------

* GUI tutorial: `booya-at.github.io/openglider-tutorial
  <https://booya-at.github.io/openglider-tutorial>`_
* FreeCAD Glider extension and workflow: see the ``freecad/glider`` source and
  ``docs_old/freecad_glider_docs/`` for screenshots and notes.

**Use at your own risk** — the workbench is maintained for compatibility with
recent FreeCAD and OpenGlider versions but may require adjustments for your setup.
