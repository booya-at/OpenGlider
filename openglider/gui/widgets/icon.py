import os
from typing import Dict

import iconify
from openglider.gui.qt import QtGui


dirname = os.path.abspath(__file__)
for _ in range(2):
    dirname = os.path.dirname(dirname)

icon_dir = os.path.join(dirname, "icons")
iconify.path.addIconDirectory(icon_dir)



_icon_cache: Dict[str, iconify.Icon] = {}

def Icon(icon_name):
    if icon_name not in _icon_cache:
        color = QtGui.QColor(255,255,255)
        icon = iconify.Icon(icon_name, color=color)

        _icon_cache[icon_name] = icon
    
    return _icon_cache[icon_name]
