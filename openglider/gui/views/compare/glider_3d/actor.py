import logging

import openglider.mesh
from openglider.glider.glider import Glider
from openglider.glider.project import GliderProject
from openglider.gui.views_3d.widgets import View3D
from openglider.gui.views_3d.actors import MeshView
from openglider.gui.views.compare.glider_3d.config import GliderViewConfig


logger = logging.getLogger(__name__)


class GliderActors:
    project: GliderProject
    glider_3d: Glider | None
    config: GliderViewConfig | None
    actors: dict[str, MeshView]

    def __init__(self, project: GliderProject):
        self.project = project
        self.glider_3d = None
        self.actors = {}
        self.config = None
        
    def get_panels(self, numribs: int) -> MeshView:
        if self.glider_3d is None:
            raise ValueError("Glider3D not set")

        panel_mesh = openglider.mesh.Mesh()

        for i, cell in enumerate(self.glider_3d.cells):
            for panel in cell.panels:
                mesh_temp = panel.get_mesh(cell, numribs=numribs)
                panel_mesh += mesh_temp

                if not (i == 0 and self.glider_3d.has_center_cell):
                    panel_mesh += mesh_temp.copy().mirror("y")

        mesh_view = MeshView()
        mesh_view.draw_mesh(panel_mesh)
        return mesh_view
    
    def get_ribs(self) -> MeshView:
        ribs_mesh = openglider.mesh.Mesh()

        if self.glider_3d is None:
            raise ValueError("Glider3D not set")

        for i, rib in enumerate(self.glider_3d.ribs):
            mesh_temp = rib.get_mesh(filled=True)

            ribs_mesh += mesh_temp

            # center cell -> dont mirror 0 and 1, no center cell -> dont mirror 0
            if i > self.glider_3d.has_center_cell:
                ribs_mesh += mesh_temp.copy().mirror("y")

        mesh_view = MeshView()
        mesh_view.draw_mesh(ribs_mesh)
        return mesh_view

    def get_lines(self) -> MeshView:
        if self.glider_3d is None:
            raise ValueError("Glider3D not set")

        mesh_lineset = self.glider_3d.lineset.get_mesh(numpoints=3)

        mesh_view = MeshView()
        mesh_view.draw_mesh(mesh_lineset + mesh_lineset.copy().mirror("y"))

        return mesh_view
    
    def get_diagonals(self) -> MeshView:
        if self.glider_3d is None:
            raise ValueError("Glider3D not set")

        mesh = openglider.mesh.Mesh()
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for diagonal in cell.diagonals:
                cell_mesh = diagonal.get_mesh(cell, 2)

                mesh += cell_mesh
                if cell_no > 0 or not self.glider_3d.has_center_cell:
                    mesh += cell_mesh.copy().mirror("y")
        
        mesh_view = MeshView()
        mesh_view.draw_mesh(mesh)
        return mesh_view

    def get_straps(self) -> MeshView:
        if self.glider_3d is None:
            raise ValueError("Glider3D not set")
            
        mesh = openglider.mesh.Mesh()
        for cell_no, cell in enumerate(self.glider_3d.cells):
            for diagonal in cell.straps:
                cell_mesh = diagonal.get_mesh(cell, 2)

                mesh += cell_mesh
                if cell_no > 0 or not self.glider_3d.has_center_cell:
                    mesh += cell_mesh.copy().mirror("y")
        
        mesh_view = MeshView()
        mesh_view.draw_mesh(mesh)
        return mesh_view

    def add(self, view_3d: View3D, config: GliderViewConfig) -> None:
        if self.glider_3d is None or config.needs_recalc(self.config):
            self.glider_3d = self.project.glider_3d.copy()

            if self.glider_3d is None:
                return
                
            self.glider_3d.profile_numpoints = config.profile_numpoints
            for rib in self.glider_3d.ribs:
                rib.get_hull()
        
            self.actors = {
                "panels": self.get_panels(config.numribs),
                "ribs": self.get_ribs(),
                "lines": self.get_lines(),
                "diagonals": self.get_diagonals(),
                "straps": self.get_straps()
            }
        
        for name in config.get_active_keys():
            view_3d.show_actor(self.actors[name])

        self.config = config.copy()

    def remove(self, view_3d: View3D) -> None:
        if self.config is None:
            return

        for name in self.config.get_active_keys():
            view_3d.renderer.RemoveActor(self.actors[name])

    def update(self, view_3d: View3D, config: GliderViewConfig) -> None:
        self.remove(view_3d)
        self.add(view_3d, config)

