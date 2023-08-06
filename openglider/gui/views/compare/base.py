from __future__ import annotations

import abc
from typing import TYPE_CHECKING
from openglider.gui.qt import QtWidgets, QtCore

if TYPE_CHECKING:
    from openglider.gui.app.app import GliderApp
#from openglider.gui.qt import QtCore


class MixinMeta(type(QtCore.QObject), abc.ABCMeta):  # type: ignore
    pass

class CompareView(object, metaclass=MixinMeta):
    def __init__(self, app: GliderApp=None, parent: QtCore.QObject=None):
        pass

    @abc.abstractmethod
    def update_view(self) -> None:
        raise NotImplementedError()
