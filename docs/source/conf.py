# -*- coding: utf-8 -*-
# OpenGlider Sphinx documentation build configuration
# This file is in docs/source/ so that sphinx-build can use docs/source as sourcedir.

import os
import sys

# Project root (parent of docs/)
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_path)

# Mock cached_property for Sphinx so openglider can be imported without side effects
import openglider.utils.cache as _cache
_cache.cached_property = lambda *a: (lambda f: property(f))

import openglider

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',      # Google/NumPy style docstrings
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = '.rst'
master_doc = 'index'

project = 'OpenGlider'
copyright = '2014–2025, booya and contributors'
release = openglider.__version__
version = release.split('-')[0] if '-' in release else release

pygments_style = 'sphinx'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
napoleon_use_param = True
napoleon_include_special_with_doc = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}

# Paths relative to this conf (docs/source/)
html_theme = 'alabaster'
html_static_path = ['_static']
html_title = f'OpenGlider {version} Documentation'
html_short_title = 'OpenGlider'
html_show_sourcelink = True
html_show_sphinx = False
htmlhelp_basename = 'opengliderdoc'

latex_elements = {
    'papersize': 'a4paper',
    'babel': '\\usepackage[english]{babel}',
}
latex_documents = [
    ('index', 'openglider.tex', 'OpenGlider Documentation', 'booya', 'manual'),
]
