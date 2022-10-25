from openglider.gui.qt import QtGui, QtCore, QtWidgets



class ToggleGroup(QtWidgets.QWidget):
    def __init__(self, options, horizontal=True) -> None:
        super().__init__()
        if horizontal:
            self.setLayout(QtWidgets.QHBoxLayout())
        else:
            self.setLayout(QtWidgets.QVBoxLayout())
        
        self.checkboxes = {}

        def get_clickhandler(prop):
            
            def toggle_prop(value):
                setattr(self.config, prop, value)
                self.changed.emit()
            
            return toggle_prop

        for prop in self.config.__annotations__:

            checkbox = QtWidgets.QCheckBox(self)
            checkbox.setChecked(getattr(self.config, prop))
            checkbox.setText(f"{prop}")
            checkbox.clicked.connect(get_clickhandler(prop))
            self.layout().addWidget(checkbox)
            self.checkboxes[prop] = checkbox
