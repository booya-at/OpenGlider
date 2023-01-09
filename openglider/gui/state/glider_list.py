from __future__ import annotations

import asyncio
import os
from typing import Generic, Type, TYPE_CHECKING
import logging
import openglider

from openglider.gui.state.selection_list.list import SelectionList, SelectionListItem, SelectionListItemT
from openglider.gui.state.selection_list.cache import Cache, CacheListType
from openglider.glider.project import GliderProject
from openglider.utils.colors import Color
from openglider.utils.dataclass import dataclass

if TYPE_CHECKING:
    from openglider.gui.views.glider_list import GliderListWidget

logger = logging.getLogger(__name__)

class GliderListItem(SelectionListItem[GliderProject]):
    mtime: float | None = None
    failed: bool = False


class GliderList(SelectionList[GliderProject, GliderListItem]):

    @classmethod
    def get_type(cls) -> Type[SelectionListItemT]:
        return GliderListItem  # type: ignore

    async def watch(self, glider_list: GliderListWidget) -> None:
        while True:
            changed = self.scan()
            if changed:
                glider_list.render()
                glider_list.changed.emit()
            await asyncio.sleep(1)

    def scan(self) -> bool:
        changed = False
        for project_name, project in self.elements.items():
            if project.element.filename:
                mtime = os.path.getmtime(project.element.filename)

                if project.mtime is not None:
                    if mtime > project.mtime:
                        try:
                            project.element = self.import_glider(project.element.filename)
                            project.failed = False
                        except Exception as e:
                            project.failed = True
                            logger.info(str(e))
                    

                        changed = True
                else:
                    logger.warning(f"no mtime set: {project.name} {mtime}")
                
                project.mtime = mtime

        return changed
    
    @staticmethod
    def import_glider(filename: str) -> GliderProject:
        if filename.endswith(".ods"):
            glider = openglider.glider.project.GliderProject.import_ods(filename)
        else:
            glider = openglider.load(filename)

        if isinstance(glider, openglider.glider.ParametricGlider):
            project = GliderProject(glider, filename=filename)
        elif isinstance(glider, GliderProject):
            project = glider
            project.filename = filename
        else:
            raise ValueError(f"cannot import {glider}")
        
        if project.name is None:
            name = os.path.split(filename)[1]
            project.name = ".".join(name.split(".")[:-1])
        
        project.glider_3d.rename_parts()

        return project
    
    def add(self, name: str, obj: GliderProject, color: Color = None, select: bool = True) -> GliderListItem:
        element = super().add(name, obj, color, select)

        if obj.filename is not None:
            mtime = os.path.getmtime(obj.filename)
            element.mtime = mtime
        
        return element


class GliderCache(Generic[CacheListType], Cache[GliderProject, CacheListType]):
    def __init__(self, elements: GliderList):
        super().__init__(elements)



