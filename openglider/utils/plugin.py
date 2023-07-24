from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import importlib
import pkgutil

if TYPE_CHECKING:
    from openglider.gui.app import GliderApp

logger = logging.getLogger(__name__)

def setup_plugins(app: GliderApp=None) -> list[str]:
    plugins = []
    installed_packages = pkgutil.iter_modules()
    for p in installed_packages:
        if p.name.startswith("openglider") and p.name != "openglider":
            print(f"using plugin: {p.name}")
            try:
                module = importlib.import_module(p.name)
                init = getattr(module, "init", None)
                if init is not None:
                    init(app)
                else:
                    logger.warning(f"no init function in plugin: {p.name}")
                
                plugins.append(p.name)
            except Exception as e:
                logger.error(str(e))
                raise e

    return plugins