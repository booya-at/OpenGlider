Getting Started
===============

After installation (see :doc:`installation`), you can use OpenGlider from
Python scripts or an interactive shell (e.g. IPython).

Quick example
-------------

Load a glider from a JSON file, inspect it, build a mesh, and export::

   import openglider

   glider = openglider.load("tests/common/demokite.json")
   print(f"Area: {glider.area} m², span: {glider.span} m")

   mesh = glider.get_mesh(midribs=2, add_lines=True)
   mesh.export_obj("glider.obj")

Save and load
-------------

Save the current glider to JSON::

   openglider.save(glider, "my_glider.json", add_meta=True)

Load from JSON or ODS (spreadsheet)::

   glider = openglider.load("my_glider.json")
   # or from a parametric ODS:
   # glider = openglider.load("project.ods")

Running tests
-------------

Tests use **pytest**. From the project root:

* **Unit tests only** (recommended for CI and quick runs; no GUI/VTK)::

     pytest tests/ -m "not visual"
     # or:  ./testall.py
     # or:  pixi run test

* **All tests** (including visual/GUI tests; may block without display)::

     pytest tests/
     # or:  ./testall.py -a
     # or:  pixi run test-all

Unit tests live in ``test_*.py``; visual tests in ``visual_test_*.py`` and are
marked with the ``visual`` marker. See the repository file ``tests/README.md``
for more commands (single file, filter by name, repeat runs).

Interactive use
---------------

OpenGlider is intended to be used as a library in scripts or interactively.
Example in a Python or IPython session::

   >>> import openglider
   >>> glider = openglider.load("tests/common/demokite.json")
   >>> for rib in glider.ribs:
   ...     rib.aoa_relative += 3
   >>> mesh = glider.get_mesh(midribs=4, add_lines=True)
   >>> mesh.export_obj("/tmp/glider.obj")

For parametric (2D) design from an ODS spreadsheet::

   >>> glider_2d = openglider.glider.ParametricGlider.import_ods("tests/common/demokite.ods")
   >>> glider_3d = glider_2d.get_glider_3d()
   >>> openglider.save(glider_3d, "glider_3d.json")

Next steps
----------

* Read :doc:`concepts` for the main data structures (Glider, Cell, Rib, LineSet).
* See :doc:`project_structure` for an overview of the ``openglider`` package.
* Use the :doc:`api/index` for detailed API reference.
