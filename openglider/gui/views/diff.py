import difflib
import logging

from openglider.glider.project import GliderProject
from openglider.gui.app.state import ApplicationState
from openglider.gui.qt import QtWebEngineWidgets, QtWidgets

logger = logging.getLogger(__name__)


class WingSelector(QtWidgets.QComboBox):
    def __init__(self, parent: QtWidgets.QWidget, state: ApplicationState):
        super().__init__(parent=parent)
        self.state = state
        self._setup_options()
    
    def _setup_options(self) -> None:
        self.setCurrentIndex(0)
        self.clear()

        self.addItem("--")
        for project in self.state.projects.elements:
            self.addItem(project)
    
    def get_selected(self) -> GliderProject | None:
        current_index = self.currentIndex()
        current_text = self.currentText()

        if len(self.state.projects) < 1 or current_index <= 0:
            return None
        
        return self.state.projects.get(current_text)


class DiffView(QtWidgets.QWidget):
    diff_view: QtWebEngineWidgets.QWebEngineView

    def __init__(self, parent: QtWidgets.QWidget, state: ApplicationState) -> None:
        super().__init__(parent)
        
        self.state = state
        self.differ = difflib.HtmlDiff(wrapcolumn=False)

        self.setLayout(QtWidgets.QVBoxLayout())

        self.choosers = QtWidgets.QWidget()
        self.choosers.setLayout(QtWidgets.QHBoxLayout())
        self.choosers.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.layout().addWidget(self.choosers)

        self.chooser_left = WingSelector(self, self.state)
        self.chooser_left.currentIndexChanged.connect(self.diff)
        self.choosers.layout().addWidget(self.chooser_left)
        self.chooser_right = WingSelector(self, self.state)
        self.chooser_right.currentIndexChanged.connect(self.diff)
        self.choosers.layout().addWidget(self.chooser_right)

        self.diff_view = QtWebEngineWidgets.QWebEngineView()
        self.layout().addWidget(self.diff_view)
    
    def update_view(self) -> None:
        self.chooser_left._setup_options()
        self.chooser_right._setup_options()
        self.diff()
    

    def diff(self) -> None:
        left_glider = self.chooser_left.get_selected()
        right_glider = self.chooser_right.get_selected()

        if left_glider is None or right_glider is None:
            self.diff_view.setHtml("<html><body><h2>Empty!</h2></body></html>")
        
        else:
            md1 = left_glider.as_markdown().split("\n")
            md2 = right_glider.as_markdown().split("\n")

            diff = self.differ.make_file(md1, md2)

            self.diff_view.setHtml(diff)

        self.diff_view.show()


    
