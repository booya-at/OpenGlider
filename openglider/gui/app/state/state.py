import os
import logging
import importlib
import datetime
from typing import List, Dict, Any

from openglider.gui.app.state.list import SelectionList

import openglider.jsonify
from openglider.utils.colors import Color
from openglider.glider.project import GliderProject
from openglider.utils.dataclass import dataclass, Field

@dataclass
class GuiProject:
    project: GliderProject
    visible: bool
    modification_time: datetime.datetime
    color: Color

    def __json__(self):
        return {
            "project": self.project,
            "visible": self.visible,
            "modification_time": str(self.modification_time),
            "color": self.color.hex()
        }
    
    @classmethod
    def __from_json__(cls, **dct):
        dct["modification_time"] = datetime.datetime.fromisoformat(dct["modification_time"])
        dct["color"] = Color.parse_hex(dct["color"])
        return cls(**dct)



@dataclass
class ApplicationState:
    projects: SelectionList[GliderProject] = Field(default_factory=lambda: SelectionList())
    opened_tabs: Dict[str, Any] = Field(default_factory=lambda: {})

    current_tab: str = ""
    current_preview: str = ""
    debug_level: int = logging.WARNING

    def __json__(self):
        return {
            "projects": self.projects,
            "opened_tabs": {tab.name: tab.__class__.__name__ for name, tab in self.opened_tabs},
            
            "current_tab": self.current_tab,
            "current_preview": self.current_preview,
            "debug_level": self.debug_level
        }
    
    def get_selected(self) -> GliderProject:
        project = self.projects.get_selected()

        if project is None:
            raise Exception("No project selected")
        
        return project
    
    def get_glider_projects(self, filter_active=False) -> List[GliderProject]:
        if filter_active:
            return self.projects.get_active()
        
        return self.projects.get_all()
    
    def add_glider_project(self, project: GliderProject):
        if project.name in self.projects:
            raise Exception(f"project with name {project.name} already in the list")
        
        self.projects.add(project.name, project)
    
    def update_glider_project(self, project: GliderProject):
        self.projects[project.name] = project
    
    def remove_glider_project(self, project: GliderProject):
        self.projects.remove(project.name)
        
    @staticmethod
    def get_tab_cls(name: str):
        path_parts = name.split(".")

        import_path = ".".join(path_parts[:-1])
        cls_name = path_parts[-1]

        module = importlib.import_module(import_path)

        return getattr(module, cls_name)

    _dump_path = "/tmp/openglider_state.json"

    def dump(self):
        with open(self._dump_path, "w") as fp:
            openglider.jsonify.dump(self, fp)
        
    @classmethod
    def load(cls):
        if os.path.isfile(cls._dump_path):
            with open(cls._dump_path, "r") as state_file:
                result = openglider.jsonify.load(state_file)

                return result["data"]
            
        return cls()


