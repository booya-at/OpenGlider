from typing import List
import functools
import os
import sys
import logging
import asyncio
import traceback

from openglider.gui.qt import QtWidgets, QtGui, QtCore
from openglider.gui.views.diff import DiffView


from qasync import QThreadExecutor

import openglider
from openglider.glider.project import GliderProject
from openglider.gui.views.compare import GliderPreview
from openglider.gui.views.glider_list import GliderList
from openglider.gui.views.tasks import QTaskQueue
from openglider.gui.views.console import LoggingConsole, ConsoleHandler
from openglider.gui.widgets.icon import Icon
from openglider.gui.app.state import ApplicationState
#from openglider.gui.views.window import Window


logger = logging.getLogger(__name__)


class Action():
    def __init__(self, main_window: "MainWindow", name, widget):
        self.name = name
        self.widget = widget
        self.main_window = main_window
        self.action = None

    def run(self):
        glider = self.main_window.state.get_selected()
        logger.info(f"open {self.name}({glider.name})")

        window = self.widget(self.main_window, glider)
        self.main_window.show_tab(window)

    def get_qt_action(self):
        if self.action is None:
            self.action = QtWidgets.QAction(Icon("substract"), self.name, self.main_window)
            self.action.triggered.connect(self.run)
        
        return self.action


class MainWindow(QtWidgets.QMainWindow):
    main_widget_class = GliderPreview

    def __init__(self, app):
        super().__init__()
        self.setWindowTitle("Glider Schneider")
        
        self.app = app
        self.state: ApplicationState = app.state

        self.actions = {}
        self.active_windows = []

        self.main_widget = QtWidgets.QSplitter()
        self.main_widget.setOrientation(QtCore.Qt.Vertical)
        

        self.top_panel = QtWidgets.QTabWidget(self.main_widget)
        self.main_widget.addWidget(self.top_panel)

        self.bottom_panel = QtWidgets.QWidget(self.main_widget)
        self.bottom_panel.setLayout(QtWidgets.QHBoxLayout())
        self.main_widget.addWidget(self.bottom_panel)

        self.main_widget.setSizes([800, 200])

        self.setCentralWidget(self.main_widget)


        
        menubar: QtWidgets.QMenuBar = self.menuBar()

        self.menus = {
            "file": menubar.addMenu("&File")
        }
        self.menu_actions = self._get_actions()

        for menu_name in self.menu_actions:
            self.menus[menu_name] = menubar.addMenu(f"&{menu_name}")

        self.menus["debug"] = menubar.addMenu(f"&Debug")
        reload_action = QtWidgets.QAction(Icon("substract"), "Reload", self)
        reload_action.triggered.connect(self.app.reload_code)
        self.menus["debug"].addAction(reload_action)

        toggle_console = QtWidgets.QAction(Icon("document"), "Toggle Console", self)
        toggle_console.setShortcut("del")  #QtGui.QKeySequence(QtCore.Qt.Key_AsciiCircum)
        #toggle_console.setStatusTip("Toggle Console")
        toggle_console.triggered.connect(self.toggle_console)
        menubar.addAction(toggle_console)

        load_glider = QtWidgets.QAction(Icon("folder"), "Open", self)
        load_glider.setShortcut("Ctrl+O")
        load_glider.setStatusTip("Load Glider")
        load_glider.triggered.connect(self.open_dialog)

        load_demokite = QtWidgets.QAction(Icon("folder"), "Demokite", self)
        load_demokite.setShortcut("Ctrl+D")
        load_demokite.setStatusTip("Load Demokite")
        load_demokite.triggered.connect(self.load_demokite)

        self.menus["file"].addAction(load_glider)
        self.menus["file"].addAction(load_demokite)

        self.glider_list = GliderList(self, self.state)
        self.glider_list.on_change.append(self.current_glider_changed)

        self.overview = QtWidgets.QWidget(self.main_widget)
        self.overview.setLayout(QtWidgets.QHBoxLayout())
        self.overview.layout().addWidget(self.glider_list, 25)

        self.glider_preview = GliderPreview(self.app)
        self.overview.layout().addWidget(self.glider_preview, 75)

        self.top_panel.addTab(self.overview, "Main")

        self.diff_view = DiffView(self, self.state)
        self.top_panel.addTab(self.diff_view, "Diff")

        self.task_queue = QTaskQueue(self, self.app.task_queue)
        self.top_panel.addTab(self.task_queue, "Tasks")

        self.console = LoggingConsole(self)
        self.bottom_panel.layout().addWidget(self.console, 75)

        self.signal_handler = ConsoleHandler(self.console)

        self.previews = {}
        self.add_actions()

        self.setAcceptDrops(True)
        self.showMaximized()
        self.current_glider_changed()


        try:
            selected_glider = self.state.get_selected()
            self.current_glider_changed(selected_glider)
        except Exception as e:
            pass
    
    def _get_actions(self):
        from openglider.gui.app.actions import menu_actions
        return menu_actions

    def show_tab(self, window):
        tab_index = self.top_panel.count()

        self.top_panel.addTab(window, window.name)
        self.top_panel.setCurrentIndex(tab_index)

        self.state.current_tab = window
        
        tabbar: QtWidgets.QTabBar = self.top_panel.tabBar()
        tabbar.setTabButton(tab_index, QtWidgets.QTabBar.RightSide, window.close_button)

        def close():
            # iterate through all closable tabs (i>=2)
            for i, tab in enumerate(self.get_opened_tabs()):
                if tab == window:
                    self.top_panel.removeTab(i+2)
                    self.top_panel.setCurrentIndex(0)
                    return
            
            # hasn't returned yet? raise!
            raise Exception(f"couldn't close tab: {window}")

        window.closed.connect(close)
    
    def toggle_console(self):
        if self.console.height() > 0:
            self.main_widget.setSizes([1000, 0])
        else:
            self.main_widget.setSizes([700, 300])

    def get_opened_tabs(self, gliderproject=None):
        for i in range(2, self.top_panel.count()):
            yield self.top_panel.widget(i)

    def update_menu(self):
        num_gliders = self.glider_list.count()

        for name, menu in self.menus.items():
            menu: QtWidgets.QMenu = menu
            menu.setEnabled(num_gliders > 0)

    def add_actions(self):
        for menu_name, actions in self.menu_actions.items():
            for widget, name in actions:
                action = Action(self, name, widget)
                qt_action = action.get_qt_action()

                self.menus[menu_name].addAction(qt_action)
                self.actions[name] = action

    def call_action(self, name):
        action = self.actions[name]
        action.run()

    
    @property
    def loop(self):
        return self.app.loop

    async def execute(self, function, *args, **kwargs):
        result = await self.app.execute(function, *args, **kwargs)
        return result
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """
        Drag and Drop glider files
        """
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            fname = None
            # Workaround for OSx dragging and dropping
            for url in e.mimeData().urls():
                #if op_sys == 'Darwin':
                #    fname = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
                fname = str(url.toLocalFile())
            
            if fname:
                if fname.endswith("hdf5"):
                    from openglider.gui.wizzards.physics.fem import FemImportTask, FemView
                    self.task_queue.append(FemImportTask(fname), FemView)
                else:
                    asyncio.create_task(self.load_glider(fname))
            #self.load_image()
        else:
            e.ignore()
    
    def process(self):
        self.app.processEvents()
    
    @property
    def glider_projects(self) -> List[GliderProject]:
        return self.state.get_glider_projects()

    def current_glider_changed(self, glider=None):
        # cleanup widgets
        self.glider_preview.update()
        self.diff_view.update()
        try:
            active_wing = self.state.get_selected()
        except Exception:
            active_wing = None
            
        self.console.push_local_ns("active_wing", active_wing)


    def add_glider(self, glider, focus=True, increase_revision=False):
        logger.info(f"Adding glider {glider.name}")

        if increase_revision:
            need_to_increase = True

            while need_to_increase:
                glider.increase_revision_nr()
                need_to_increase = False
                for project in self.glider_projects:
                    if glider.name == project.name:
                        need_to_increase = True
            
            logger.info(f"new name: {glider.name}")
        
        self.state.add_glider_project(glider)
        self.state.selected_project = glider.name
        self.glider_list.render()

        self.console.push_local_ns("wings", list(self.glider_projects))
        self.current_glider_changed(glider)
        self.update_menu()
        self.top_panel.setCurrentIndex(0)

    def run_action(self, name):
        glider = self.glider_list.current_glider
        widget = self.previews[glider]
        return widget.run_action(name)

    async def load_fem_case(self, filename):
        logger.info(f"load gpufem case: {filename}")
        glider = self.glider_list.current_glider
        if glider is None:
            logger.error("No glider loaded for hdf5 analysis")
            return

        from openglider.gui.wizzards.physics.fem import FemView
        case = await FemView.load_gpu_case(self, glider, filename)
        self.show_tab(case)

    def load_demokite(self):
        og_dir = os.path.dirname(os.path.dirname(openglider.__file__))
        filename = os.path.join(og_dir, "tests/common/demokite.ods")
        asyncio.create_task(self.load_glider(filename))


    def open_dialog(self):
        home = os.path.expanduser("~")
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "load glider", home, filter="Openglider (*.ods *.json)")

        if filename:
            asyncio.create_task(self.load_glider(filename))


    async def load_glider(self, filename: str):
        project = await self.execute(self.glider_list.import_glider, filename)

        logger.info(f"add glider: {project.name}")
        self.add_glider(project)
    
    def closeEvent(self, event):
        """
        Ask to save unsaved gliders
        """
        unsaved_gliders = [p for p in self.glider_projects if p.filename is None]

        close = True

        if len(unsaved_gliders):
            msgBox = QtWidgets.QMessageBox()
            
            msgBox.setText("Unsaved Gliders")
            msgBox.setWindowTitle("Discard Changes?")

            text = "\n".join(["   - "+p.name for p in unsaved_gliders])
            msgBox.setInformativeText(text)

            msgBox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
            ret = msgBox.exec_()

            if ret == QtWidgets.QMessageBox.Save:
                event.ignore()
                close = False
            else:
                event.accept()
                #sys.exit(0)

        if self.task_queue.queue.is_busy():
            msgBox = QtWidgets.QMessageBox()
            
            msgBox.setText("Running Tasks")
            msgBox.setWindowTitle("Stop?")

            text = "\n".join(["   - "+p.name for p in unsaved_gliders])
            msgBox.setInformativeText(text)

            msgBox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)

            ret = msgBox.exec_()

            if ret == QtWidgets.QMessageBox.Save:
                event.ignore()
                close = False
            else:
                self.app.loop.run_until_complete(self.task_queue.queue.quit())
                event.accept()
                #sys.exit(0)
        
        
