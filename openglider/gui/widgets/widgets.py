from collections.abc import Callable
from openglider.gui.qt import QtWidgets


class WindowSwitcher(QtWidgets.QWidget):
    widgets: dict[str, QtWidgets.QWidget]
    
    def __init__(self, target_widget: QtWidgets.QWidget) -> None:
        super().__init__()
        self.target_widget = target_widget

        self.target_widget_layout = QtWidgets.QStackedLayout()
        self.target_widget.setLayout(self.target_widget_layout)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.selector = QtWidgets.QComboBox()
        self.selector.activated.connect(self.show_widget)
        layout.addWidget(self.selector)

        self.widgets = {}

    def add_window(self, name: str, widget: QtWidgets.QWidget, show: bool=True) -> None:
        if name in self.widgets:
            self.target_widget_layout.removeWidget(widget)
        else:
            self.selector.addItem(name)

        self.widgets[name] = widget
        self.target_widget_layout.addWidget(widget)

    def show_widget(self, widget_name: str) -> None:
        widget = self.widgets[widget_name]
        self.selector.setCurrentText(widget_name)
        self.target_widget_layout.setCurrentWidget(widget)


class InputLabel(QtWidgets.QWidget):
    _text: str
    _active: bool
    on_change: list[Callable[[str], None]]

    def __init__(self) -> None:
        super().__init__()
        self._layout = QtWidgets.QStackedLayout()
        self.setLayout(self._layout)

        self.label = QtWidgets.QLabel()
        self.input = QtWidgets.QLineEdit()

        self.input.returnPressed.connect(self.apply)

        self._layout.addWidget(self.label)
        self._layout.addWidget(self.input)
        self._layout.setCurrentWidget(self.label)

        self._text = ""
        self._active = False
        self.on_change = []

    def apply(self) -> None:
        self._active = False
        self._layout.setCurrentWidget(self.label)
        if self.input.isModified():
            print("jo, new")
            self.text = self.input.text()
            for f in self.on_change:
                f(self.text)

    def edit(self) -> None:
        if self._active:
            return
        
        self._active = True

        self._layout.setCurrentWidget(self.input)

    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self.label.setText(text)
        self.input.setText(text)