Installation
============

OpenGlider can be installed with pip, pixi, or conda. For development, use an
editable install so the code and docs stay in sync.

pip (recommended)
-----------------

From the project root::

   git clone https://github.com/booya-at/OpenGlider.git
   cd OpenGlider
   pip install -e .

This installs OpenGlider in editable mode. After pulling from the repository,
your environment stays up to date.

Dependencies (install with pip or your system package manager as needed):

* ezodf2
* dxfwrite
* scipy
* numpy
* (optional) svgwrite, vtk, FreeCAD for GUI and visualisation

pixi
----

If you use `pixi <https://pixi.sh>`_, from the project root run::

   pixi run freecad

to launch FreeCAD with OpenGlider installed in the environment.

conda
-----

Conda packages are provided via conda-forge::

   conda create -n openglider openglider freecad meshpy -c conda-forge

Manual / development install
-----------------------------

Clone the repository, then either::

   python setup.py develop

for a linked install (recommended for development), or::

   python setup.py install

for a static install.

Building the documentation
--------------------------

From the project root::

   pip install sphinx sphinx-rtd-theme  # or use your env)
   cd docs
   make html

The HTML output is in ``docs/build/html/``. Open ``index.html`` in a browser.
