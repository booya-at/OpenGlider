import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui


def _clear():
    mw = Gui.getMainWindow()
    editor = mw.findChild(QtGui.QPlainTextEdit, "Python console")
    report = mw.findChild(QtGui.QTextEdit, "Report view")
    editor.clear()
    report.clear()

Gui.clear = _clear


# glider commands

class activeGlider(object):
    def __init__(self):
        self._update()

    def _update(self):
        sel = Gui.Selection.getSelection()
        if len(sel) == 1:
            obj = sel[0]
            if hasattr(obj, "Proxy") and hasattr(obj.Proxy, 'getGliderInstance'):
                self._glider = obj
                return
        self._glider = None

    @property
    def glider(self):
        self._update()
        return self._glider

    @property
    def ParametricGlider(self):
        return self.glider.Proxy.getParametricGlider()

    @property
    def GliderInstance(self):
        return self.glider.Proxy.getGliderInstance()

    @property
    def visuals(self):
        return self.glider.ViewObject

    def apply(self):
        self._update()
        if self._glider:
            self.ParametricGlider.get_glider_3d(self.GliderInstance)
            self.visuals.Proxy.updateData()
            App.ActiveDocument.recompute()

    def __repr__(self):
        if self.glider:
            return self.GliderInstance.__repr__()
        else:
            return "No Glider selected"

    def addCut(self, pos, cells=None):
        if cells == None:
            cells = range(self.ParametricGlider.shape.half_cell_num)
        cut = {
            "left": pos,
            "right": pos,
            "cells": cells,
            "type": "orthogonal"
        }
        self.ParametricGlider.elements["cuts"].append(cut)


ActiveGlider = activeGlider()
