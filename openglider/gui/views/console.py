import os
import logging

from openglider.gui.qt import QtGui, QtCore

import openglider
from pyqtconsole.console import PythonConsole

logging.getLogger("openglider")

    
class LoggingConsole(PythonConsole):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.push_local_ns("openglider", openglider)
        self.push_local_ns("app", self.app)
        self.push_local_ns("wings", [])
        self.push_local_ns("active_wing", None)

        self.eval_queued()

    def log(self, message):
        lines_no = message.count("\n")

        cursor = self._textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(message)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

        self._prompt_doc[-1] = ""
        self._prompt_doc += [""] * lines_no
        for line in self._prompt_doc[-lines_no:]:
             self.pbar.adjust_width(line)
        
        self._output_inserted = True
        self._update_ps(False)
        self._show_ps()


class QSignaler(QtCore.QObject):
    log_message = QtCore.Signal(str)


class ConsoleHandler(logging.Handler):
    emitter = QtCore.Signal(str)
    """Logging handler to emit to LoggingConsole"""

    def __init__(self, console: LoggingConsole, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.console = console
        self.signal = QSignaler()

        # make it thread safe
        self.signal.log_message.connect(self.console.log)

        self.setFormatter(logging.Formatter(
            fmt="{asctime} {levelname} ({name}): {message}",
            datefmt="%H:%M:%S",
            style="{"
            ))
        
        self.add_logger("openglider")
        self.add_logger("gpufem")
    
    def add_logger(self, name):
        logger = logging.getLogger(name)
        logger.addHandler(self)

    def emit(self, record):
        if record.levelno < 20:
            return

        msg = self.format(record)
        self.signal.log_message.emit(msg)

        
        #self.console.log(msg)
