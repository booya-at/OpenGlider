import FreeCADGui as Gui
import FreeCAD


Gui.addIconPath(FreeCAD.getHomePath()+"Mod/glider/icons")

from shape import ChangeShape
from examples import LoadGlider
from profiles import LoadProfile, ChangeProfile, RunXfoil, CompareProfile, MergeProfile

Gui.addCommand('LoadGlider', LoadGlider())
Gui.addCommand('ChangeShape', ChangeShape())
Gui.addCommand('LoadProfile', LoadProfile())
Gui.addCommand('ChangeProfile', ChangeProfile())
Gui.addCommand('RunXfoil', RunXfoil())
Gui.addCommand('CompareProfile', CompareProfile())
Gui.addCommand('MergeProfile', MergeProfile())