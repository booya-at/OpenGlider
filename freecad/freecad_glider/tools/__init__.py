import os

import FreeCAD
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui

try:
    from importlib import reload
except ImportError:
    App.Console.PrintError('this is python2\n')
    App.Console.PrintWarning('there is a newer version (python3)\n')
    App.Console.PrintMessage('try to motivate dev to port to python3\n')

from . import _glider as glider
from . import _tools as tools
from . import airfoil_tool
from . import shape_tool
from . import arc_tool
from . import span_mapping
from . import ballooning_tool
from . import line_tool
from . import panel_method as pm
from . import cell_tool
from . import design_tool
from . import color_tool
from . import features
import openglider
from openglider import jsonify


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
        Gui.Control.showDialog(self.tool(self.glider_obj))
    
    @property
    def glider_obj(self):
        obj = Gui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                return obj
        return None

    @property
    def feature(self):
        obj = Gui.Selection.getSelection()
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
        Gui.activeDocument().activeView().setCameraType("Perspective")
        cam = Gui.ActiveDocument.ActiveView.getCameraNode()
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
                'MenuText': 'export 2D',
                'ToolTip': 'export 2D'}

    def Activated(self):
        obj = self.glider_obj
        if obj:
            tools.export_2d(obj)


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
        Gui.SendMsgToActiveView('ViewFit')
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
        obj = Gui.Selection.getSelection()
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
                'ToolTip': 'import glider'}

    def IsActive(self):
        return (FreeCAD.ActiveDocument is not None)

    def Activated(self):
        self.create_glider_with_dialog()


class ShapeCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'shape_command.svg',
                'MenuText': 'shape',
                'ToolTip': 'shape'}

    def tool(self, obj):
        return shape_tool.ShapeTool(obj)


class ArcCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'arc_command.svg',
                'MenuText': 'arc',
                'ToolTip': 'arc'}

    def tool(self, obj):
        return arc_tool.ArcTool(obj)


class AoaCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'aoa_command.svg',
                'MenuText': 'aoa',
                'ToolTip': 'aoa'}

    def tool(self, obj):
        return span_mapping.AoaTool(obj)


class ZrotCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'z_rot_command.svg',
                'MenuText': 'zrot',
                'ToolTip': 'zrot'}

    def tool(self, obj):
        return span_mapping.ZrotTool(obj)


class AirfoilCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'airfoil_command.svg',
                'MenuText': 'airfoil',
                'ToolTip': 'airfoil'}

    def tool(self, obj):
        return airfoil_tool.AirfoilTool(obj)


class AirfoilMergeCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'airfoil_merge_command.svg',
                'MenuText': 'airfoil merge',
                'ToolTip': 'airfoil merge'}

    def tool(self, obj):
        return span_mapping.AirfoilMergeTool(obj)


class BallooningCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_command.svg',
                'MenuText': 'ballooning',
                'ToolTip': 'ballooning'}

    def tool(self, obj):
        return ballooning_tool.BallooningTool(obj)


class BallooningMergCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_merge_command.svg',
                'MenuText': 'ballooning merge',
                'ToolTip': 'ballooning merge'}

    def tool(self, obj):
        return span_mapping.BallooningMergeTool(obj)


class LineCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'line_command.svg',
                'MenuText': 'lines',
                'ToolTip': 'lines'}

    def tool(self, obj):
        return line_tool.LineTool(obj)


class LineObserveCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'line_observe.svg',
                'MenuText': 'line observe',
                'ToolTip': 'line observe'}

    def tool(self, obj):
        return line_tool.LineObserveTool(obj)


def check_glider(obj):
    if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'getGliderInstance'):
        return True


class PanelCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'panel_method.svg',
                'MenuText': 'panelmethode', 
                'ToolTip': 'panelmethode'}

    def tool(self, obj):
        return pm.PanelTool(obj)

class PolarsCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'polar.svg', 'MenuText': 'polars', 'ToolTip': 'polars'}

    def tool(self, obj):
        return pm.Polars(obj)


class CutCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'cut_command.svg', 'MenuText': 'Design', 'ToolTip': 'Design'}

    def tool(self, obj):
        return design_tool.DesignTool(obj)

class ColorCommand(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'color_selector.svg', 'MenuText': 'Design', 'ToolTip': 'Colors'}

    def tool(self, obj):
        return color_tool.ColorTool(obj)


class RefreshCommand():
    NOT_RELOAD = ["freecad.freecad_glider.init_gui"]
    RELOAD = ["pivy.coin", "freecad.freecad_glider"]
    def GetResources(self):
        return {'Pixmap': 'refresh_command.svg', 'MenuText': 'Refresh', 'ToolTip': 'Refresh'}

    def IsActive(self):
        return True

    def Activated(self):
        import sys
        for name, mod in sys.modules.items():
            for rld in self.RELOAD:
                if rld in name:
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
        return {'Pixmap': 'rib_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'set airfoil to ribs'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'ribFeature')
        self.feature.ViewObject.Visibility = False
        features.RibFeature(feature, self.glider_obj)
        vp = features.VRibFeature(feature.ViewObject)
        vp.updateData()


class GliderBallooningFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'set ballooning to ribs'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'ballooningFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.BallooningFeature(feature, self.glider_obj)
        vp = features.VBallooningFeature(feature.ViewObject)
        vp.updateData()


class GliderSharkFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'sharknose_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'shark nose'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'sharkFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.SharkFeature(feature, self.glider_obj)
        vp = features.VSharkFeature(feature.ViewObject)
        vp.updateData()

class GliderSingleSkinRibFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'singleskin_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'set single-skin feature'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'singleSkinRib')
        self.glider_obj.ViewObject.Visibility = False
        features.SingleSkinRibFeature(feature, self.glider_obj)
        vp = features.VSingleSkinRibFeature(feature.ViewObject)
        vp.updateData()

class GliderFlapFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'flap_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'flap feature'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'flapFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.FlapFeature(feature, self.glider_obj)
        vp = features.VFlapFeature(feature.ViewObject)
        vp.updateData()

class GliderHoleFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'hole_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'hole feature'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'holeFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.HoleFeature(feature, self.glider_obj)
        vp = features.VHoleFeature(feature.ViewObject)
        vp.updateData()

class GliderScaleFeatureCommand(GliderFeatureCommand):
    def GetResources(self):
        return {'Pixmap': 'scale_feature.svg' , 'MenuText': 'Features', 'ToolTip': 'scale feature'}

    def Activated(self):
        feature = FreeCAD.ActiveDocument.addObject('App::FeaturePython', 'scaleFeature')
        self.glider_obj.ViewObject.Visibility = False
        features.ScaleFeature(feature, self.glider_obj)
        vp = glider.OGGliderVP(feature.ViewObject)
        vp.updateData()