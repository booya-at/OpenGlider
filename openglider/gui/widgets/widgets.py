from openglider.gui.qt import QtWidgets, QtCore


class WindowSwitcher(QtWidgets.QWidget):
    def __init__(self, target_widget):
        super(WindowSwitcher, self).__init__()
        self.target_widget = target_widget

        self.target_widget_layout = QtWidgets.QStackedLayout()
        self.target_widget.setLayout(self.target_widget_layout)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.selector = QtWidgets.QComboBox()
        self.selector.activated[str].connect(self.show_widget)
        self.layout().addWidget(self.selector)

        self.widgets = {}

    def add_window(self, name, widget, show=True):
        if name in self.widgets:
            self.target_widget_layout.removeWidget(widget)
        else:
            self.selector.addItem(name)

        self.widgets[name] = widget
        self.target_widget_layout.addWidget(widget)

    def show_widget(self, widget_name):
        widget = self.widgets[widget_name]
        self.selector.setCurrentText(widget_name)
        self.target_widget_layout.setCurrentWidget(widget)


class InputLabel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QStackedLayout())

        self.label = QtWidgets.QLabel()
        self.input = QtWidgets.QLineEdit()

        self.input.returnPressed.connect(self.apply)

        self.layout().addWidget(self.label)
        self.layout().addWidget(self.input)
        self.layout().setCurrentWidget(self.label)

        self._text = ""
        self._active = False
        self.on_change = []

    def apply(self):
        self._active = False
        self.layout().setCurrentWidget(self.label)
        if self.input.isModified():
            print("jo, new")
            self.text = self.input.text()
            for f in self.on_change:
                f(self.text)

    def edit(self):
        if self._active:
            return
        
        self._active = True

        self.layout().setCurrentWidget(self.input)

    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, text):
        self._text = text
        self.label.setText(text)
        self.input.setText(text)