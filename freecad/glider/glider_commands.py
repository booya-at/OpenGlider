import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui


def _clear():
    """Clear the FreeCAD Python console and report view.

    This is registered as ``Gui.clear`` and is mainly used by the
    OpenGlider workbench to reset textual output.
    """
    mw = Gui.getMainWindow()
    editor = mw.findChild(QtGui.QPlainTextEdit, "Python console")
    report = mw.findChild(QtGui.QTextEdit, "Report view")
    editor.clear()
    report.clear()


Gui.clear = _clear


# glider commands


class activeGlider(object):
    """Helper around the currently selected glider object in FreeCAD.

    The instance tracks the active document selection and offers
    convenience accessors to the parametric and 3D glider as well
    as helper methods to apply changes.
    """

    def __init__(self):
        """Create a helper bound to the current FreeCAD selection."""
        self._update()

    def _update(self):
        """Refresh internal reference to the currently selected glider."""
        sel = Gui.Selection.getSelection()
        if len(sel) == 1:
            obj = sel[0]
            if hasattr(obj, "Proxy") and hasattr(obj.Proxy, "getGliderInstance"):
                self._glider = obj
                return
        self._glider = None

    @property
    def glider(self):
        """Return the selected FreeCAD glider object or ``None``."""
        self._update()
        return self._glider

    @property
    def ParametricGlider(self):
        """Return the associated :class:`ParametricGlider` instance."""
        return self.glider.Proxy.getParametricGlider()

    @property
    def GliderInstance(self):
        """Return the associated 3D :class:`Glider` instance."""
        return self.glider.Proxy.getGliderInstance()

    @property
    def visuals(self):
        """Return the ViewObject used for 3D visualisation."""
        return self.glider.ViewObject

    def apply(self):
        """Recompute the 3D glider from parametric data and update the view."""
        self._update()
        if self._glider:
            self.ParametricGlider.get_glider_3d(self.GliderInstance)
            self.visuals.Proxy.updateData()
            App.ActiveDocument.recompute()

    def __repr__(self):
        """Return a human readable representation for debugging."""
        if self.glider:
            return self.GliderInstance.__repr__()
        else:
            return "No Glider selected"

    def addCut(self, pos, cells=None):
        """Add an orthogonal cut definition to the parametric glider.

        Parameters
        ----------
        pos : float
            Spanwise position of the cut in the parametric space.
        cells : iterable[int] or None
            Indices of cells to which the cut applies. If ``None``,
            all half-cells of the current shape are used.
        """
        if cells is None:
            cells = range(self.ParametricGlider.shape.half_cell_num)
        cut = {"left": pos, "right": pos, "cells": cells, "type": "orthogonal"}
        self.ParametricGlider.elements["cuts"].append(cut)


#: Global helper bound to the current FreeCAD selection.
ActiveGlider = activeGlider()
