from openglider.gui.qt import QtWidgets, QtCore

class Input(QtWidgets.QWidget):
    def __init__(self, parent=None, name=None, default=None, vertical=False):
        super().__init__(parent=parent)
        self.name = name
        
        self.on_change = []
        self.on_changed = []

        if vertical:
            layout = QtWidgets.QVBoxLayout()
        else:
            layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        label = QtWidgets.QLabel(name)
        layout.addWidget(label)

        self.input = QtWidgets.QLineEdit(parent=self)
        if default is not None:
            self.set_value(default, propagate=True)
        self.input.setObjectName(name)

        layout.addWidget(self.input)

        self.input.textChanged.connect(self._on_change)
        self.input.editingFinished.connect(self._on_changed)
    
    def set_value(self, value, propagate=False):
        self.value = value
        if propagate:
            self.input.setText(str(value))

    def _on_change(self, text):
        print(f"change: {text}")
        self.set_value(text)
        for f in self.on_change:
            f(self.value)

    def _on_changed(self):
        self.input.setText(str(self.value))
        for f in self.on_changed:
            f(self.value)


class NumberInput(Input):
    def __init__(self, parent=None, name=None, min_value=None, max_value=None, places=None, default=None, vertical=False):
        self.min_value = min_value
        self.max_value = max_value
        self.places = places
        super().__init__(parent, name, default, vertical)

    def set_value(self, value, propagate=False):
        value = float(value)
        if self.min_value is not None:
            value = max(self.min_value, value)

        if self.max_value is not None:
            value = min(self.max_value, value)

        if self.places is not None:
            value = round(value, self.places)
        
        super().set_value(value, propagate)

        