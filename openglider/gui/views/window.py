from __future__ import annotations

import logging
import typing

from openglider.glider.project import GliderProject
from openglider.gui.qt import QtCore, QtGui, QtWidgets

if typing.TYPE_CHECKING:
    from openglider.gui.app.main_window import MainWindow


logger = logging.getLogger(__name__)

class Window(QtWidgets.QWidget):
    closed = QtCore.Signal(int)
    widget_name: str = ""
    app: MainWindow

    def __init__(self, app: MainWindow):
        super().__init__()
        self.app = app

        self.icon = QtGui.QIcon.fromTheme("window-close")
        self.close_button = QtWidgets.QToolButton()
        self.close_button.setIcon(self.icon)

        self.close_button.clicked.connect(self.close)


    @classmethod
    def get_class_name(cls) -> str:
        if cls.widget_name:
            return cls.widget_name

        return cls.__name__

    @property
    def name(self) -> str:
        return f"{self.get_class_name()}"

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        logger.info(f"closing {self}")
        super().closeEvent(event)
        self.closed.emit(0)


class GliderWindow(Window):
    project: GliderProject
    
    copy_project = True

    def __init__(self, app: MainWindow, project: GliderProject):
        super().__init__(app)

        if self.copy_project:
            self.project = project.copy()
        else:
            self.project = project

    @property
    def name(self) -> str:
        return f"{self.get_class_name()}: {self.project.name}"
