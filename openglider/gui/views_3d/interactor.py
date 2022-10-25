import vtk



class Interactor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self):
        super(Interactor, self).__init__()
        self.AddObserver("MiddleButtonPressEvent",self.middleButtonPressEvent)
        self.AddObserver("MiddleButtonReleaseEvent",self.middleButtonReleaseEvent)
        self.AddObserver("RightButtonPressEvent",self.rightButtonPressEvent)
        self.AddObserver("RightButtonReleaseEvent",self.rightButtonReleaseEvent)

    def middleButtonPressEvent(self,obj,event):
        self.OnRightButtonDown()
        return

    def middleButtonReleaseEvent(self,obj,event):
        self.OnRightButtonUp()
        return

    def rightButtonPressEvent(self,obj,event):
        self.OnMiddleButtonDown()
        return

    def rightButtonReleaseEvent(self,obj,event):
        self.OnMiddleButtonUp()
        return