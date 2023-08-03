from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, List, Optional, Type, TypeVar
import logging
import asyncio

from openglider.gui.qt import QtGui, QtWidgets, QtCore

from openglider.utils.tasks import TaskQueue, Task
from openglider.gui.widgets.icon import Icon
from openglider.gui.views.window import Window

if TYPE_CHECKING:
    from openglider.gui.app.app import GliderApp
    from openglider.gui.app.main_window import MainWindow


logger = logging.getLogger(__name__)


Td = QtWidgets.QTableWidgetItem

class TaskWindow(Window):
    task: Task
    def __init__(self, app: MainWindow, task: Task):
        self.task = task
        super().__init__(app)


class QTaskListWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, app: MainWindow, task: Task, view: type[TaskWindow] | None):
        super().__init__(parent)
        self.task = task
        self.app = app
        self.view_class = view

        self.setLayout(QtWidgets.QHBoxLayout())
        self.label_status = QtWidgets.QLabel()
        self.label_name = QtWidgets.QLabel(self.task.get_name())
        self.label_runtime = QtWidgets.QLabel()

        self.button_view = QtWidgets.QToolButton()
        self.button_view.setIcon(Icon("plus"))

        if self.view_class is None:
            self.button_view.setDisabled(True)
        else:
            self.button_view.clicked.connect(self.open_widget)

        self.layout().addWidget(self.label_status)
        self.layout().addWidget(self.label_name)
        self.layout().addWidget(self.label_runtime)
        self.layout().addWidget(self.button_view)

        self.update()
    
    def update(self, *args: Any, **kwargs: Any) -> None:
        button = "database-1"
        if self.task.finished:
            button = "checked"
        elif self.task.running:
            button = "play-button"

        if self.task.failed:
            button = "dislike"

        icon = Icon(button)
        self.label_status.setPixmap(icon.pixmap(QtCore.QSize(40, 40)))

        self.label_runtime.setText(self.task.runtime())
    
    def open_widget(self) -> None:
        if self.view_class is not None:
            view = self.view_class(self.app, self.task)
        
            self.app.show_tab(view)
        


class QTaskEntry(QtWidgets.QListWidgetItem):
    def __init__(self, parent: QtWidgets.QWidget, app: MainWindow, task: Task, view: type[TaskWindow] | None):
        super().__init__()
        self.app = app
        self.task = task
        self.widget = QTaskListWidget(parent, app, task, view)

        self.setSizeHint(self.widget.sizeHint())

    def update(self) -> None:
        self.widget.update()





class QTaskQueue(QtWidgets.QWidget):
    tasks: list[QTaskEntry]

    app: MainWindow
    queue: TaskQueue

    def __init__(self, app: MainWindow, queue: TaskQueue):
        super().__init__()
        self.app = app
        self.queue = queue
    
        self.setLayout(QtWidgets.QVBoxLayout())

        self.list = QtWidgets.QListWidget(self)
        self.list.setDragEnabled(True)
        
        self.layout().addWidget(self.list)
        self.update_task = asyncio.create_task(self._update())

        self.tasks = []

    def append(self, task: Task, view: type[TaskWindow] | None = None) -> None:
        list_entry = QTaskEntry(self.list, self.app, task, view)

        self.tasks.append(list_entry)
        self.list.addItem(list_entry)
        self.list.setItemWidget(list_entry, list_entry.widget)

        self.queue.tasks.append(task)
        # self.app.show_tab(self)

    async def _update(self) -> None:
        while True:
            for entry in self.tasks:
                entry.update()
            await asyncio.sleep(1)

    def close(self, *args: Any, **kwargs: Any) -> None:  # type: ignore
        #self.update_task.cancel()
        super().close(*args, **kwargs)


