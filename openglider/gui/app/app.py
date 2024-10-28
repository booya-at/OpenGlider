from __future__ import annotations

import asyncio
import functools
import importlib
import io
import logging
import os
import sys
import time
import traceback
from types import TracebackType
from typing import TYPE_CHECKING, Any
from collections.abc import Callable

import pyqtgraph  # fix strange error by loading it before qtmodern
import qtmodern.styles
import qtmodern.windows
from openglider.gui.qt import QtWidgets
from openglider.gui.app.files import OpengliderDir
from qasync import QEventLoop

if TYPE_CHECKING:
    from openglider.gui.app.state import ApplicationState

logger = logging.getLogger(__name__)


class GliderApp(QtWidgets.QApplication):
    debug = False
    exception_window: QtWidgets.QMessageBox | None = None
    state: ApplicationState

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.setApplicationName("GliderSchneider")
        qtmodern.styles.dark(self)

        log_format = '%(levelname)s %(asctime)s - %(name)s : %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_format, datefmt="%d-%m-%y %H:%M")
        logger.info(f"Current working directory: {os.getcwd()}")

        logger.info("Start event loop")
        self.loop = QEventLoop(self)
        asyncio.set_event_loop(self.loop)


        sys.excepthook = self.show_exception

        self.setup()
    
    def setup(self) -> None:
        logger.info("Load modules")
        import openglider.gui.app.main_window
        import openglider.gui.app.state
        import openglider.utils.tasks
        from openglider.utils.plugin import setup_plugins

        logger.info("Setup plugins")
        plugins = setup_plugins(self)

        openglider.gui.app.state.ApplicationState.model_rebuild()
        self.state = openglider.gui.app.state.ApplicationState.load()
        self.task_queue = openglider.utils.tasks.TaskQueue(self.execute)
        #self.task_queue = openglider.utils.tasks.TaskQueue()
        self.task_queue.exception_hook = self.show_exception
        self.main_window = openglider.gui.app.main_window.MainWindow(self)

        for plugin in plugins:
            self.main_window.signal_handler.add_logger(plugin)


        logger.info("Show main window")
        self.main_window.showMaximized()
    
    def reload_code(self) -> None:
        self.main_window.close()
        self.state.dump()

        #self._deep_reload("euklid")
        #self._deep_reload("openglider", "gpufem")
        self._deep_reload("openglider")

        # TODO: check!
        # for x in list(pydantic.class_validators._FUNCS):
        #     if x.startswith("openglider"):
        #         pydantic.class_validators._FUNCS.remove(x)


        self.setup()

    @staticmethod
    def _deep_reload(*names: str) -> None:
        for module in list(sys.modules.keys()):
            if any([module.startswith(folder) for folder in names]):
                del sys.modules[module]
        
        # And then you can reimport the file that you are running.
        for module in names:
            importlib.import_module(module)
    
    def run(self) -> None:
        with self.loop:
            self.loop.run_forever()


    async def execute(self, function: Callable[[Any], Any], *args: Any, **kwargs: Any) -> Any:
        if args or kwargs:
            func = functools.partial(function, *args, **kwargs)
        else:
            func = function  # type: ignore

        #with QThreadExecutor(1) as pool:
        try:
            if self.debug:
                data = func()
            else:
                data = await self.loop.run_in_executor(None, func)
            return data
        except Exception as e:
            logger.error("fuck")
            logger.error(e)
            self.show_exception(*sys.exc_info())
            #raise e

    def show_exception(self, exception_type: type[BaseException], exception_value: BaseException, tracebackobj: TracebackType | None) -> Any:
        """
        Global function to catch unhandled exceptions.

        @param exception_type exception type
        @param exception_value exception value
        @param tracebackobj traceback object
        """
        separator = '- - ' * 20

        notice = "\n" * 3 + "Exception!"
        time_string = time.strftime("%d.%m.%Y  %H:%M:%S")

        traceback_io = io.StringIO()
        traceback.print_tb(tracebackobj, None, traceback_io)
        traceback_io.seek(0)
        traceback_message = traceback_io.read()

        errmsg = f'{str(exception_type)}: \t{str(exception_value)}'
        message = "\n".join([
            notice,
            time_string,
            separator,
            errmsg,
            separator,
            f"Written to log-file in {OpengliderDir.base_path}"
        ])

        try:
            with OpengliderDir.logfile("a+") as logfile:
                logfile.write("\n".join([
                    notice,
                    time_string,
                    separator,
                    errmsg,
                    separator,
                    traceback_message,
                    separator
                ]))
        except OSError:
            pass

        self.exception_window = QtWidgets.QMessageBox()
        self.exception_window.setText(message)
        self.exception_window.setDetailedText(traceback_message)
        self.exception_window.show()
        #errorbox.exec_()
