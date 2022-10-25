from typing import List
import logging
import asyncio

from openglider.gui.qt import QtGui, QtWidgets, QtCore

from openglider.utils.tasks import TaskQueue, Task
from openglider.gui.widgets.icon import Icon

logger = logging.getLogger(__name__)


Td = QtWidgets.QTableWidgetItem


class QTaskListWidget(QtWidgets.QWidget):
    view = None
    view_class = None

    def __init__(self, parent, app, task, view):
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
    
    def setup_views(self):
        from openglider.gui.wizzards.physics.flow.openfoam import FoamView, GliderFoamCase
        self.views = {
            GliderFoamCase: FoamView,
        }

    def update(self):
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
    
    def open_widget(self):
        view = self.view_class(self.app, self.task)
        
        self.app.show_tab(view)
        


class QTaskEntry(QtWidgets.QListWidgetItem):
    def __init__(self, parent, app, task: Task, view):
        super().__init__(parent)
        self.app = app
        self.task = task
        self.widget = QTaskListWidget(parent, app, task, view)

        self.setSizeHint(self.widget.sizeHint())

    def update(self):
        self.widget.update()





class QTaskQueue(QtWidgets.QWidget):
    tasks: List[Task]

    def __init__(self, app, queue: TaskQueue):
        super().__init__()
        self.app = app
        self.queue = queue
    
        self.setLayout(QtWidgets.QVBoxLayout())

        self.list = QtWidgets.QListWidget(self)
        self.list.setDragEnabled(True)
        
        self.layout().addWidget(self.list)
        self.update_task = asyncio.create_task(self._update())

        self.tasks = []

    def append(self, task: Task, view=None):
        list_entry = QTaskEntry(self.list, self.app, task, view)

        self.tasks.append(list_entry)
        self.list.addItem(list_entry)
        self.list.setItemWidget(list_entry, list_entry.widget)

        self.queue.tasks.append(task)
        # self.app.show_tab(self)

    async def _update(self):
        while True:
            for entry in self.tasks:
                entry.update()
            await asyncio.sleep(1)

    def close(self, *args, **kwargs):
        #self.update_task.cancel()
        super().close(*args, **kwargs)


