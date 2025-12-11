========================
OpenGlider Documentation
========================

Installation
------------

The fastest way is to use pip2 if installed on your system::

    git clone https://github.com/hiaselhans/OpenGlider.git
    cd OpenGlider
    pip2 install -e .

this will install a linked version of openglider on your system. If you
pull from the repository the installation will be up to date.
Also you might want to install vtk or freecad from your systems package manager.

Manual way is as follows:

install all dependencies first:
    * ezodf(2)
    * dxfwrite
    * scipy
    * (svgwrite)
    * (vtk)

clone the repo::

    git clone https://github.com/hiaselhans/OpenGlider.git


and install using setup.py::

    cd OpenGlider
    python2 setup.py install

(developers choice)::

    python2 setup.py develop

Contents:

.. toctree::

    source/getting_started
    source/project_structure
    source/developer

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

