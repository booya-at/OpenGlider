from PyQt4 import QtCore, QtGui
import Graphics.QVTKRenderWindowInteractor as vq
import sys
import vtk

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        
        self.widget = QtGui.QWidget()
        self.widget.setGeometry(QtCore.QRect(40, 20, 191, 161))
        self.widget.setObjectName(_fromUtf8("widget"))
        #self.widget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())
        #self.widget.Initialize()
        #self.widget.Start()
        #ren = vtk.vtkRenderer()
        #self.widget.GetRenderWindow().AddRenderer(ren)
        #cone = vtk.vtkConeSource()
        """cone.SetResolution(8)
        coneMapper = vtk.vtkPolyDataMapper()
        coneMapper.SetInput(cone.GetOutput())
        coneActor = vtk.vtkActor()
        coneActor.SetMapper(coneMapper)
        ren.AddActor(coneActor)"""
        
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(290, 160, 91, 27))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.pushButton_2 = QtGui.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(280, 60, 91, 27))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.pushButton.setText(_translate("Dialog", "PushButton", None))
        #self.pushButton_2.setText(_translate("Dialog", "PushButton", None))
        
class MyDialog(QtGui.QDialog, Ui_Dialog):
    def __init__(self):
        super(MyDialog, self).__init__()
        self.setupUi(self)
# show the widget
app = QtGui.QApplication(sys.argv)
w= MyDialog()
w.show()
# start event processing
app.exec_()
