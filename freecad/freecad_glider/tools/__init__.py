import os

import FreeCAD
import FreeCADGui
import openglider
from openglider import jsonify
from PySide import QtGui

from . import glider
from . import tools
from . import (airfoil_tool, arc_tool, ballooning_tool, cell_tool, color_tool,
               design_tool, features, line_tool)
from . import panel_method as pm
from . import shape_tool, span_mapping

try:
    from importlib import reload
except ImportError:
    FreeCAD.Console.PrintError('this is python2\n')
    FreeCAD.Console.PrintWarning('there is a newer version (python3)\n')
    FreeCAD.Console.PrintMessage('try to motivate dev to port to python3\n')



#   -import export                                          -?
#   -construction (shape, arc, lines, aoa, ...)             -blue
#   -simulation                                             -yellow
#   -optimisation                                           -red


# Commands-------------------------------------------------------------

class BaseCommand(object):
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': '.svg', 'MenuText': 'Text', 'ToolTip': 'Text'}

    def IsActive(self):
        if (FreeCAD.ActiveDocument is not None and self.glider_obj):
            return True

    def Activated(self):
        tool = self.tool(self.glider_obj)
        #################################################################################
        # Diese Funktionen sind nur zur Strukturierung und nicht zwingend noetig.
        # deswegen sollten sie intern im __init__ aufgerufen werden.
        # Ausser es gibt einen Grund des extern zu machen. 
        # tool.setup_widget()
        # tool.setup_pivy()
        ##################################################################################
        FreeCADGui.Control.showDialog(tool)
    
    @property
    def glider_obj(self):
        obj = FreeCADGui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                return obj
        return None

    @property
    def feature(self):
        obj = FreeCADGui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                return obj
        return None

    def tool(self, obj):
        return tools.BaseTool(obj)


class ViewCommand(object):
    def GetResources(self):
        return {'Pixmap': 'cell_command.svg',
                'MenuText': 'edit cells',
                'ToolTip': 'edit cells'}

    def IsActive(self):
        return True

    def Activated(self):
        FreeCADGui.activeDocument().activeView().setCameraType("Perspective")
        cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
        cam.heightAngle = 0.4


class CellCommand(BaseCommand):
    def tool(self, obj):
        return cell_tool.CellTool(obj)

    def GetResources(self):
        return {'Pixmap': 'cell_command.svg',
                'MenuText': 'edit cells',
                'ToolTip': 'edit cells'}


class Gl2dExport(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'gl2d_export.svg',
                'MenuText': 'export glider',
                'ToolTip': 'export glider (different formats)'}

    def Activated(self):
        proceed = False
        obj = FreeCADGui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                proceed = True
        if proceed:
            glider_2d = obj.Proxy.getParametricGlider()
            glider_3d = obj.Proxy.getGliderInstance()
            tools.export_glider(glider_2d, glider_3d)


class CreateGlider(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'new_glider.svg',
                'MenuText': 'create glider',
                'ToolTip': 'create glider'}

    @staticmethod
    def create_glider(import_path=None, parametric_glider=None):
        glider_object = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'Glider')
        glider.OGGlider(glider_object, import_path=import_path, parametric_glider=parametric_glider)
        vp = glider.OGGliderVP(glider_object.ViewObject)
        vp.updateData()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView('ViewFit')
        return glider_object


    def IsActive(self):
        return (FreeCAD.ActiveDocument is not None)

    def Activated(self):
        CreateGlider.create_glider()


class PatternCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'pattern_command.svg',
                'MenuText': 'unwrap glider',
                'ToolTip': 'unwrap glider'}

    def Activated(self):
        proceed = False
        obj = FreeCADGui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                proceed = True
        if proceed:
            from openglider import plots
            file_name = QtGui.QFileDialog.getSaveFileName(
                parent=None,
                caption='create panels',
                directory='~')
            if not file_name[0] == '':
                file_name = file_name[0]
                pat = plots.Patterns(obj.Proxy.getParametricGlider())
                pat.unwrap(file_name, obj.Proxy.getGliderInstance())

    @staticmethod
    def fcvec(vec):
        return FreeCAD.Vector(vec[0], vec[1], 0.)


class ImportGlider(BaseCommand):
    def create_glider_with_dialog(self):
        file_name = QtGui.QFileDialog.getOpenFileName(
            parent=None,
            caption='import glider',
            directory='~')
        if file_name[0].endswith('.json'):
            if self.glider_obj:
                # replace current active par-glider with the imported par-glider
                with open(file_name[0], 'r') as importfile:
                    self.glider_obj.Proxy.setParametricGlider(jsonify.load(importfile)['data'])
            else:
                # no active glider: create a new one
                CreateGlider.create_glider(import_path=file_name[0])
        elif file_name[0].endswith('ods'):
            par_glider = openglider.glider.ParametricGlider.import_ods(file_name[0])
            if self.glider_obj:
                # replace current active par-glider with the imported par-glider
                self.glider_obj.Proxy.setParametricGlider(par_glider)
            else:
                # no active glider: create a new one
                CreateGlider.create_glider(parametric_glider=par_glider)
        else:
            FreeCAD.Console.PrintError('\nonly .ods and .json are supported')

    def GetResources(self):
        return {'Pixmap': 'import_glider.svg',
                'MenuText': 'import glider',
                'ToolTip': 'import glider from different formats'}

    def IsActive(self):
        return (FreeCAD.ActiveDocument is not None)

    def Activated(self):
        self.create_glider_with_dialog()


class ShapeCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'shape_command.svg',
                'MenuText': 'shape',
                'ToolTip': 'modify shape'}

    def tool(self, obj):
        return shape_tool.ShapeTool(obj)


class ArcCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'arc_command.svg',
                'MenuText': 'arc',
                'ToolTip': 'modify arc'}

    def tool(self, obj):
        return arc_tool.ArcTool(obj)


class AoaCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'aoa_command.svg',
                'MenuText': 'angle-of-attack',
                'ToolTip': 'modify angle of attack'}

    def tool(self, obj):
        return span_mapping.AoaTool(obj)


class ZrotCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'z_rot_command.svg',
                'MenuText': 'z-rotation',
                'ToolTip': 'modify rib-z-rotation'}

    def tool(self, obj):
        return span_mapping.ZrotTool(obj)


class AirfoilCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'airfoil_command.svg',
                'MenuText': 'airfoils',
                'ToolTip': 'create/modify airfoil (deprecated, use airfoil-workbench instead)'}

    def tool(self, obj):
        return airfoil_tool.AirfoilTool(obj)

    def IsActive(self):
        if (FreeCAD.ActiveDocument is not None and self.glider_obj):
            parent_obj = self.glider_obj.Proxy.getParent()
            print(parent_obj)
            if hasattr(parent_obj, "airfoils"):
                    if len(parent_obj.airfoils) != 0:
                        return False
            return True



class AirfoilMergeCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'airfoil_merge_command.svg',
                'MenuText': 'airfoil-distribution',
                'ToolTip': 'distribute airfoils in span direction'}

    def tool(self, obj):
        return span_mapping.AirfoilMergeTool(obj)


class BallooningCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_command.svg',
                'MenuText': 'ballooning',
                'ToolTip': 'create/modify ballooning distributions'}

    def tool(self, obj):
        return ballooning_tool.BallooningTool(obj)


class BallooningMergCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_merge_command.svg',
                'MenuText': 'ballooning-distribution',
                'ToolTip': 'distribute ballooning-distributions in span direction'}

    def tool(self, obj):
        return span_mapping.BallooningMergeTool(obj)


class LineCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'line_command.svg',
                'MenuText': 'lines',
                'ToolTip': 'create/modify lines'}

    def tool(self, obj):
        return line_tool.LineTool(obj)


class LineObserveCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'line_observe.svg',
                'MenuText': 'line-observe',
                'ToolTip': 'check/observe line-forces and lengths'}

    def tool(self, obj):
        return line_tool.LineObserveTool(obj)


def check_glider(obj):
    if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'getGliderInstance'):
        return True


class PanelCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'panel_method.svg',
                'MenuText': 'panel-method', 
                'ToolTip': 'compute aerodynamic properties with potential-flow'}

    def tool(self, obj):
        return pm.PanelTool(obj)

class PolarsCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'polar.svg', 
        'MenuText': 'polars', 'ToolTip': 'polars'}

    def tool(self, obj):
        return pm.Polars(obj)


class CutCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'cut_command.svg', 
                'MenuText': 'Design', 
                'ToolTip': 'cut cells for coloring and openings'}

    def tool(self, obj):
        return design_tool.DesignTool(obj)

class ColorCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'color_selector.svg', 
                'MenuText': 'Colors', 
                'ToolTip': 'Modify color of Panels'}

    def tool(self, obj):
        return color_tool.ColorTool(obj)


class RefreshCommand():
    NOT_RELOAD = ["freecad.freecad_glider.init_gui"]
    RELOAD = ["pivy.coin", "freecad.freecad_glider"]
    def GetResources(self):
        return {'Pixmap': 'refresh_command.svg',
                'MenuText': 'Refresh',
                'ToolTip': 'Refresh openglider functionality (development)'}

    def IsActive(self):
        return True

    def Activated(self):
        import sys
        mod_names = list(sys.modules.keys())
        for name in mod_names:
            for rld in self.RELOAD:
                if rld in name:
                    mod = sys.modules[name]
                    if mod and name not in self.NOT_RELOAD:
                        print('reload {}'.format(name))
                        reload(mod)
        from pivy import coin



class GliderFeatureCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'feature.svg', 'MenuText': 'Features', 'ToolTip': 'Features'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'BaseFeature')
        self.feature.ViewObject.Visibility = False
        features.BaseFeature(feature, self.feature)
        vp = glider.OGGliderVP(feature.ViewObject)
        vp.updateData()

    def IsActive(self):
        if (FreeCAD.ActiveDocument is not None and self.feature):
            return True


class GliderRibFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'rib_feature.svg' ,
                'MenuText': 'RibFeature',
                'ToolTip': 'explicitly apply airfoils to ribs'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'ribFeature')
        self.feature.ViewObject.Visibility = False
        features.RibFeature(feature, self.glider_obj)
        vp = features.VRibFeature(feature.ViewObject)
        vp.updateData()


class GliderBallooningFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_feature.svg' , 
                'MenuText': 'BallooningFeature',
                'ToolTip': 'explicitly apply ballooning to ribs'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'ballooningFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.BallooningFeature(feature, self.glider_obj)
        vp = features.VBallooningFeature(feature.ViewObject)
        vp.updateData()


class GliderSharkFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'sharknose_feature.svg' ,
                'MenuText': 'SharknoseFeature',
                'ToolTip': 'create a shark nose'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'sharkFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.SharkFeature(feature, self.glider_obj)
        vp = features.VSharkFeature(feature.ViewObject)
        vp.updateData()

class GliderSingleSkinRibFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'singleskin_feature.svg' , 
                'MenuText': 'SingleskinFeature', 
                'ToolTip': 'create single-skin ribs (bows between attachment-points)'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'singleSkinRib')
        self.glider_obj.ViewObject.Visibility = False
        features.SingleSkinRibFeature(feature, self.glider_obj)
        vp = features.VSingleSkinRibFeature(feature.ViewObject)
        vp.updateData()

class GliderFlapFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'flap_feature.svg' , 
                'MenuText': 'FlapFeatures', 
                'ToolTip': 'modify/shorten the trailing edge'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'flapFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.FlapFeature(feature, self.glider_obj)
        vp = features.VFlapFeature(feature.ViewObject)
        vp.updateData()

class GliderHoleFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'hole_feature.svg' , 
                'MenuText': 'create holes', 
                'ToolTip': 'create holes (single-skin)'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'holeFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.HoleFeature(feature, self.glider_obj)
        vp = features.VHoleFeature(feature.ViewObject)
        vp.updateData()

class GliderScaleFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'scale_feature.svg' , 
                'MenuText': 'ScaleFeatures', 
                'ToolTip': 'scale a glider by 1D-factor'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'scaleFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.ScaleFeature(feature, self.glider_obj)
        vp = glider.OGGliderVP(feature.ViewObject)
        FreeCAD.ActiveDocument.recompute()

class GliderBallooningMultiplierFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_feature.svg' , 
                'MenuText': 'BallooningMultiplyFeature', 
                'ToolTip': 'multiply balloonings by a scaling factor'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'ballooningFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.BallooningMultiplier(feature, self.glider_obj)
        vp = features.VBallooningFeature(feature.ViewObject)
        vp.updateData()

class ImportDXFCommand(object):
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'dxf_command.svg', 'MenuText': 'fast dxf import', 'ToolTip': 'fast dxf import'}

    def Activated(self):

        import numpy as np
        from . import dxf_import as dxf
        import Part
        import FreeCAD as App

        file_name = QtGui.QFileDialog.getOpenFileName(
            parent=None,
            caption='import glider',
            directory='~')
        if file_name[0].endswith('.dxf'):
            entries, results = dxf.prase(file_name[0])
            geometries = []
            for ln in results:
                if hasattr(ln, 'is_line'):
                    geometries.append(ln.toEdge())

            comp = Part.Compound(geometries)
            Part.show(comp)
