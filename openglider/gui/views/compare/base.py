import abc
from openglider.gui.qt import QtWidgets
#from openglider.gui.qt import QtCore

QObjectMeta = type(QtWidgets.QWidget)

class MixinMeta(abc.ABCMeta, QObjectMeta):  # type: ignore
    pass

class CompareView(abc.ABC, QtWidgets.QWidget, metaclass=MixinMeta):
    @abc.abstractmethod
    def update_view(self) -> None:
        raise NotImplementedError()
