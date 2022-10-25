from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets  # type: ignore
else:
    from qtpy import QtWidgets, QtCore, QtGui, QtWebEngineWidgets