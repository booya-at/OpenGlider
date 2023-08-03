from typing import Any
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera


class Interactor(vtkInteractorStyleTrackballCamera):
    def __init__(self) -> None:
        super().__init__()
        self.AddObserver("MiddleButtonPressEvent",self.middleButtonPressEvent)
        self.AddObserver("MiddleButtonReleaseEvent",self.middleButtonReleaseEvent)
        self.AddObserver("RightButtonPressEvent",self.rightButtonPressEvent)
        self.AddObserver("RightButtonReleaseEvent",self.rightButtonReleaseEvent)

    def middleButtonPressEvent(self, obj: Any,event: Any) -> None:
        self.OnRightButtonDown()
        return

    def middleButtonReleaseEvent(self, obj: Any,event: Any) -> None:
        self.OnRightButtonUp()
        return

    def rightButtonPressEvent(self, obj: Any,event: Any) -> None:
        self.OnMiddleButtonDown()
        return

    def rightButtonReleaseEvent(self, obj: Any,event: Any) -> None:
        self.OnMiddleButtonUp()
        return