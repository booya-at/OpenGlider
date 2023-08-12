from __future__ import annotations

import os
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from openglider.gui.state.glider_list import GliderList
import openglider.jsonify
from openglider.glider.project import GliderProject
from openglider.utils.dataclass import BaseModel, Field

if TYPE_CHECKING:
    pass


class ApplicationState(BaseModel):
    projects: GliderList = Field(default_factory=lambda: GliderList())
    opened_tabs: dict[str, Any] = Field(default_factory=lambda: {})

    current_tab: str = ""
    current_preview: str = ""
    debug_level: int = logging.WARNING

    def __json__(self) -> dict[str, Any]:
        return {
            "projects": self.projects,
            "opened_tabs": {tab.name: tab.__class__.__name__ for tab in self.opened_tabs.values()},
            
            "current_tab": self.current_tab,
            "current_preview": self.current_preview,
            "debug_level": self.debug_level
        }

    def add_glider_project(self, project: GliderProject) -> None:
        if project.name in self.projects:
            raise Exception(f"project with name {project.name} already in the list")
        
        self.projects.add(project.name, project)
    
    def update_glider_project(self, project: GliderProject) -> None:
        self.projects[project.name] = project
    
    def remove_glider_project(self, project: GliderProject) -> None:
        self.projects.remove(project.name)

    _dump_path: ClassVar[str] = "/tmp/openglider_state.json"

    def dump(self) -> None:
        with open(self._dump_path, "w") as fp:
            openglider.jsonify.dump(self, fp)
        
    @classmethod
    def load(cls) -> ApplicationState:
        if os.path.isfile(cls._dump_path):
            with open(cls._dump_path) as state_file:
                result = openglider.jsonify.load(state_file)

                return result["data"]
            
        return cls()
