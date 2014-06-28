import FreeCADGui as Gui
import FreeCAD


Gui.addIconPath(FreeCAD.getHomePath() + "Mod/glider_gui/icons")

from profiles import CreatePoint

Gui.addCommand('CreatePoint', CreatePoint())