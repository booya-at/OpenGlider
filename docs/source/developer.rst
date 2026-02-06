Developer Guide
===============

Contributing
------------

Contributions are welcome. Areas that need work include:

* Code quality and refactoring
* Documentation and docstrings
* Unit tests and visual tests
* New features and bug fixes

Code conventions
----------------

* Use **Python 3**-compatible code::

     print("use print as a function")

* Follow **PEP 8** where applicable: https://pep8.org/
* Write tests for new or changed behaviour.

Running tests
-------------

From the project root::

   ./testall.py

For visual tests as well::

   ./testall.py -a

Building documentation
----------------------

From the ``docs`` directory::

   make apidoc   # regenerate API .rst from openglider
   make html     # build HTML (runs apidoc automatically)

Output is in ``docs/build/html/``. Use ``sphinx-build -W`` for strict
warnings (e.g. in CI).

API documentation
-----------------

The API docs are generated from the source with ``sphinx-apidoc``. To improve
the generated docs:

* Add module and class docstrings.
* Use Google- or NumPy-style docstrings so ``sphinx.ext.napoleon`` can parse
  them.

See the :doc:`api/index` for the current API reference.
