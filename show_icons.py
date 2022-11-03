#!/bin/python
import os
import sys

from qtpy import QtWidgets, QtCore
import iconify
import iconify.browser

icon_dir = os.path.join(os.path.dirname(__file__), "openglider/gui/icons")

iconify.path.addIconDirectory(icon_dir)


app = QtWidgets.QApplication([])

browser = iconify.browser.Browser()
browser.show()

sys.exit(app.exec())
