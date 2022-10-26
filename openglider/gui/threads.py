import logging
from openglider.gui.qt import QtCore

class Signals(QtCore.QObject):
    logging = QtCore.Signal(tuple)
    finished = QtCore.Signal(bool)
    error = QtCore.Signal(tuple)

class Thread(QtCore.QRunnable):
    name = None
    
    def __init__(self, signals: Signals | None=None) -> None:
        if signals is None:
            signals = Signals()
        
        self.signals = signals
        super().__init__()
    
    def finish(self) -> None:
        self.signals.finished.emit(True)

    def log(self, message: str, level: int=logging.INFO) -> None:
        name = self.name
        if name is None:
            name = self.__class__.__name__
        self.signals.logging.emit((name, message, level))

    def autoDelete(self) -> bool:
        return True