import FreeCADGui as Gui

Gui.addIconPath("/usr/lib/freecad/Mod/glider/icons")

from shape import ChangeShape
from examples import LoadGlider
from profiles import LoadProfile, ChangeProfile

Gui.addCommand('LoadGlider', LoadGlider())
Gui.addCommand('ChangeShape', ChangeShape())
Gui.addCommand('LoadProfile', LoadProfile())
Gui.addCommand('ChangeProfile', ChangeProfile())