from __future__ import division
from __future__ import absolute_import
from meshpy.triangle import MeshInfo

import meshpy._triangle as internals


def custom_triangulation(mesh_info, opts=""):
    """Triangulate the domain given in `mesh_info'."""
    try:
        import locale
    except ImportError:
        have_locale = False
    else:
        have_locale = True
        prev_num_locale = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, "C")

    try:
        mesh = MeshInfo()
        internals.triangulate(opts, mesh_info, mesh, MeshInfo(), None)
    finally:
        # restore previous locale if we've changed it
        if have_locale:
            locale.setlocale(locale.LC_NUMERIC, prev_num_locale)

    return mesh
