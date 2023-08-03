from asyncio.log import logger
from typing import List, Optional
from collections.abc import Callable
from openglider.gui.qt import QtWidgets, QtCore


class Slider(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget=None, name: str=None, min_value: int=0, max_value: int=10, default: int | None=None, vertical: bool=False) -> None:
        super().__init__(parent=parent)
        self.name = name
        self.slider_min = min_value
        self.slider_max = max_value

        if vertical:
            layout: QtWidgets.QVBoxLayout | QtWidgets.QHBoxLayout = QtWidgets.QVBoxLayout()
        else:
            layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        label = QtWidgets.QLabel(name)
        layout.addWidget(label)

        self.slider = QtWidgets.QSlider(parent=self)
        self.slider.setTickPosition(self.slider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        if name is not None:
            self.slider.setObjectName(name)
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)

        layout.addWidget(self.slider)

        self.display = QtWidgets.QLabel(parent=self)
        layout.addWidget(self.display)

        if default is None:
            default = min_value

        self.set_bounds(min_value, max_value)
        self.set_value(default)

        self.slider.valueChanged.connect(self._set_label)
        self._set_label()

    def set_bounds(self, min_value: int=0, max_value: int=10) -> None:
        self.slider_min = min_value
        self.slider_max = max_value
        self.slider.setMinimum(min_value)
        self.slider.setMaximum(max_value)
        if self.value > max_value:
            self.slider.setValue(max_value)
            self._set_label()
        if self.value < min_value:
            self.slider.setValue(min_value)
            self._set_label()

    def _set_label(self) -> None:
        self.display.setText(f"{self.value}")

    def on_change(self, f: Callable[[int], None]) -> None:
        self.slider.valueChanged.connect(f)

    def on_release(self, f: Callable[[int], None]) -> None:
        self.slider.sliderReleased.connect(f)

    @property
    def value(self) -> int:
        return self.get_value()
    
    @value.setter
    def value(self, value: int) -> None:
        self.set_value(value)

    def get_value(self) -> int:
        return self.slider.value()

    def set_value(self, value: int) -> None:
        if self.slider_min <= value <= self.slider_max:
            self.slider.setValue(value)
            self._set_label()
        else:
            raise ValueError(f"{value} is not in bounds ({self.slider_min} / {self.slider_max})")

    def set_enabled(self, enable: bool=True) -> None:
        self.slider.setEnabled(enable)  


class FloatSlider(Slider):
    def __init__(self, parent: QtWidgets.QWidget=None, name: str="", min_value: float=0.0, max_value: float=1., steps: int=20, default: float | None=None):
        self.min = min_value
        self.max = max_value
        steps = int(steps) - 1

        assert steps >= 2
        self.steps = steps

        if default is None:
            default = min_value

        super().__init__(parent, name, 0, steps, default=default)  # type: ignore
        self.set_value(default)

    def _set_label(self) -> None:
        self.display.setText(f"{self.value:.2}")

    def get_value(self) -> float:  # type: ignore
        value = self.slider.value()
        return self.min + (self.max - self.min) * float(value) / self.steps

    def set_value(self, value) -> float:  # type: ignore
        dx = (value - self.min) / (self.max - self.min)

        super().set_value(int(self.steps * dx))


class ExpSlider(Slider):
    values: list[int]

    def __init__(self, parent: QtWidgets.QWidget=None, name: str="", min_value: int=0, max_value: int=3, steps: int=20, default: int| None=None):
        #assert min_value >= 0
        #assert max_value > 0
        linrange = [1]+{
            4: [2, 4, 7],
            5: [2, 3, 5, 7]
        }[steps]
        num_values = steps*(max_value-min_value)+1
        self.values = []

        for i in range(num_values):
            exponent = int(i / steps) + min_value
            mantisse = linrange[i%steps]
            self.values.append(mantisse*10**exponent)

        super().__init__(parent, name, 0, num_values-1, default)

    def get_value(self) -> int:
        index = self.slider.value()
        return self.values[index]

    def set_value(self, value: int) -> None:
        index = self._get_value_index(value)
        self.slider.setValue(index)
        self._set_label()
    
    def _get_value_index(self, value: int) -> int:
        value_index = 0
        min_distance = float("inf")
        for i, x in enumerate(self.values):
            distance = abs(x-value)
            if distance < min_distance:
                min_distance = distance
                value_index = i
        
        return value_index


    def _set_label(self) -> None:
        self.display.setText(f"{self.value:.01e}")