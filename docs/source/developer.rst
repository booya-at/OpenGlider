Developer Guide
===============

Contributing
------------

Contributions are welcome. Areas that need work include:

* Code quality and refactoring
* Documentation and docstrings
* Unit tests (``test_*.py``) and visual tests (``visual_test_*.py``)
* New features and bug fixes

Code conventions
----------------

* Use **Python 3**-compatible code::

     print("use print as a function")

* Follow **PEP 8** where applicable: https://pep8.org/
* Write tests for new or changed behaviour.

Running tests
-------------

Tests use **pytest**. Install test deps: ``pip install -e ".[test]"`` or use the
pixi environment. From the project root:

* **Unit tests only** (default; excludes visual/GUI tests; use for CI)::

     pytest tests/ -m "not visual"
     ./testall.py
     pixi run test

* **All tests** (including ``visual_test_*.py``; needs display/VTK)::

     pytest tests/
     ./testall.py -a
     pixi run test-all

* **Single file or filter**: ``pytest tests/test_glider.py -v``,
  ``pytest tests/ -k "glider" -v``, ``./testall.py -p "glider"``.

Visual tests are marked with the ``visual`` marker (see ``pyproject.toml`` and
``tests/conftest.py``). Full details: ``tests/README.md`` in the repository.

Building documentation
----------------------

From the project root (with pixi or ``pip install sphinx``)::

   pixi run docs
   # or:  sphinx-build -b html docs/source docs/build/html

Output is in ``docs/build/html/``. From the ``docs/`` directory you can also
use ``make apidoc`` (regenerate API .rst) and ``make html``. Use
``sphinx-build -W`` for strict warnings (e.g. in CI).

API documentation
-----------------

The API docs are generated from the source with ``sphinx-apidoc``. To improve
the generated docs:

* Add module and class docstrings.
* Use Google- or NumPy-style docstrings so ``sphinx.ext.napoleon`` can parse
  them.

See the :doc:`api/index` for the current API reference.
