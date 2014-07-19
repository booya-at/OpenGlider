from _base import ControlPointContainer
from PySide import QtCore, QtGui
import FreeCADGui as gui
import sys

def check_glider(obj):
    if "gliderinstance" in obj.PropertiesList:
        return(obj)
    else:
        return False

class base_tool(object):
    def __init__(self, obj):
        self.obj = obj
        self.form = QtGui.QWidget()
        self.setup_widget()
        self.pivy_obj = self.add_pivy()
        self.add_event_handler()

    def setup_widget(self):
        layout = QtGui.QVBoxLayout(self.form)
        self.form.setWindowTitle("base widget")
        self.btn = QtGui.QPushButton('Button', self.form)
        layout.addWidget(self.btn)


    def add_pivy(self):
        pass

    def add_event_handler(self):
        pass