from typing import Any, List
from openglider.gui.qt import QtGui, QtCore, QtWidgets


class FlowLayout(QtWidgets.QLayout):
    itemList: List[QtWidgets.QWidget]
    
    def __init__(self, parent: QtWidgets.QWidget=None, margin: int=0, spacing: int=-1):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)
        self.margin = margin
        
        # spaces between each item
        self.spaceX = 5
        self.spaceY = 5

        self.itemList = []

    def __del__(self) -> None:
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QtWidgets.QWidget) -> None:  # type: ignore
        self.itemList.append(item)

    def count(self) -> int:
        return len(self.itemList)

    def itemAt(self, index: int) -> QtWidgets.QWidget | None:  # type: ignore
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index: int) -> QtWidgets.QWidget | None:  # type: ignore
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self) -> QtCore.Qt.Orientation:
        return QtCore.Qt.Orientation.Horizontal

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect: QtCore.QRect) -> None:
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self) -> QtCore.QSize:
        return self.minimumSize()

    def minimumSize(self) -> QtCore.QSize:
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin, 2 * self.margin)
        return size

    def doLayout(self, rect: QtCore.QRect, testOnly: bool) -> int:
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            # spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            # spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + self.spaceX
            if nextX - self.spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + self.spaceY
                nextX = x + item.sizeHint().width() + self.spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()
