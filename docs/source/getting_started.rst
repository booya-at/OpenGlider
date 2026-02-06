Getting Started
===============

After installation (see :doc:`installation`), you can use OpenGlider from
Python scripts or an interactive shell (e.g. IPython).

Quick example
-------------

Load a glider from a JSON file, inspect it, build a mesh, and export::

   import openglider

   glider = openglider.load("tests/demokite.json")
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

To run the test suite (including visual tests)::

   ./testall.py -a

Run from the project root directory.

Interactive use
---------------

OpenGlider is intended to be used as a library in scripts or interactively.
Example in a Python or IPython session::

   >>> import openglider
   >>> glider = openglider.load("tests/demokite.json")
   >>> for rib in glider.ribs:
   ...     rib.aoa_relative += 3
   >>> mesh = glider.get_mesh(midribs=4, add_lines=True)
   >>> mesh.export_obj("/tmp/glider.obj")

For parametric (2D) design from an ODS spreadsheet::

   >>> glider_2d = openglider.glider.ParametricGlider.import_ods("tests/demokite.ods")
   >>> glider_3d = glider_2d.get_glider_3d()
   >>> openglider.save(glider_3d, "glider_3d.json")

Next steps
----------

* Read :doc:`concepts` for the main data structures (Glider, Cell, Rib, LineSet).
* See :doc:`project_structure` for an overview of the ``openglider`` package.
* Use the :doc:`api/index` for detailed API reference.
