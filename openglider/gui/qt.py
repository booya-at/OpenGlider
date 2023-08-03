from typing import TYPE_CHECKING

if TYPE_CHECKING:
    #from qtpy import QtWidgets, QtCore, QtGui, QtWebEngineWidgets
    from PySide6 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets  # type: ignore
    from PySide6.QtGui import QAction  # type: ignore
else:
    from qtpy import QtWidgets, QtCore, QtGui, QtWebEngineWidgets  # noqa
    from qtpy.QtWidgets import QAction  # noqa
