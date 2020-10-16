import os

from pivy import coin

try:
    import FreeCADGui as Gui
    import FreeCAD
except ImportError:
    print('module not loaded with freecad')




Dir = os.path.abspath(os.path.dirname(__file__))
Gui.addIconPath(os.path.join(Dir, 'icons'))


class GliderWorkbench(Gui.Workbench):
    MenuText = 'Glider'
    ToolTip = 'Glider Workbench'
    Icon = os.path.join(Dir, 'icons', 'glider_workbench.svg')
    toolBox = [
        'CreateGlider',
        'ImportGlider',
        'ShapeCommand',
        'ArcCommand',
        'AoaCommand',
        'ZrotCommand',
        'AirfoilCommand',
        'AirfoilMergeCommand',
        'BallooningCommand',
        'BallooningMergeCommand',
        'CellCommand',
        'LineCommand',
        'LineObserveCommand',
        'CutCommand',
        'ColorCommand',
        'Gl2dExport']

    featureBox = [
        'GliderRibFeatureCommand',
        'GliderBallooningFeatureCommand',
        'GliderSharkFeatureCommand',
        'GliderSingleSkinRibFeatureCommand',
        'GliderHoleFeatureCommand',
        'GliderFlapFeatureCommand',
        'GliderScaleFeatureCommand',
        'GliderBallooningMultiplierFeatureCommand']

    productionBox = [
        'PatternCommand',
        'PanelCommand',
        'PolarsCommand',
        'ImportDXFCommand']

    viewBox = [
        'ViewCommand']

    devBox = [
        'RefreshCommand']


    def GetClassName(self):
        return 'Gui::PythonWorkbench'

    def Initialize(self):
        from . import tools
        global Dir

        Gui.addCommand('CreateGlider', tools.CreateGlider())
        Gui.addCommand('ShapeCommand', tools.ShapeCommand())
        Gui.addCommand('AirfoilCommand', tools.AirfoilCommand())
        Gui.addCommand('ArcCommand', tools.ArcCommand())
        Gui.addCommand('AoaCommand', tools.AoaCommand())
        Gui.addCommand('BallooningCommand', tools.BallooningCommand())
        Gui.addCommand('LineCommand', tools.LineCommand())
        Gui.addCommand('LineObserveCommand', tools.LineObserveCommand())

        Gui.addCommand('ImportGlider', tools.ImportGlider())
        Gui.addCommand('Gl2dExport', tools.Gl2dExport())
        Gui.addCommand('AirfoilMergeCommand', tools.AirfoilMergeCommand())
        Gui.addCommand('BallooningMergeCommand', tools.BallooningMergCommand())
        Gui.addCommand('CellCommand', tools.CellCommand())
        Gui.addCommand('ZrotCommand', tools.ZrotCommand())
        Gui.addCommand('CutCommand', tools.CutCommand())
        Gui.addCommand('ColorCommand', tools.ColorCommand())

        Gui.addCommand('PatternCommand', tools.PatternCommand())
        Gui.addCommand('PanelCommand', tools.PanelCommand())
        Gui.addCommand('PolarsCommand', tools.PolarsCommand())

        Gui.addCommand('GliderRibFeatureCommand', tools.GliderRibFeatureCommand())
        Gui.addCommand('GliderBallooningFeatureCommand', tools.GliderBallooningFeatureCommand())
        Gui.addCommand('GliderSharkFeatureCommand', tools.GliderSharkFeatureCommand())
        Gui.addCommand('GliderSingleSkinRibFeatureCommand', tools.GliderSingleSkinRibFeatureCommand())
        Gui.addCommand('GliderHoleFeatureCommand', tools.GliderHoleFeatureCommand())
        Gui.addCommand('GliderFlapFeatureCommand', tools.GliderFlapFeatureCommand())
        Gui.addCommand('GliderScaleFeatureCommand', tools.GliderScaleFeatureCommand())
        Gui.addCommand('GliderBallooningMultiplierFeatureCommand', tools.GliderBallooningMultiplierFeatureCommand())
        Gui.addCommand('ImportDXFCommand', tools.ImportDXFCommand())

        Gui.addCommand('ViewCommand', tools.ViewCommand())

        Gui.addCommand('RefreshCommand', tools.RefreshCommand())

        self.appendToolbar('GliderTools', self.toolBox)
        self.appendToolbar('Production', self.productionBox)
        self.appendToolbar('Feature', self.featureBox)
        self.appendToolbar('GliderView', self.viewBox)
        self.appendToolbar('Develop', self.devBox)

        self.appendMenu('GliderTools', self.toolBox)
        self.appendMenu('Production', self.productionBox)
        self.appendMenu('Feature', self.featureBox)
        self.appendToolbar('GliderView', self.viewBox)
        self.appendToolbar('Develop', self.devBox)

        Gui.addPreferencePage(Dir + '/ui/preferences.ui', 'glider')

    def Activated(self):
        if not hasattr(self, "first_startup"):
            FreeCAD.Console.PrintMessage('This is the glider-workbench, a gui for openglider:\n')
            FreeCAD.Console.PrintMessage('Dynamic graphical elements can be used with:\n')
            FreeCAD.Console.PrintMessage('g...grap element and move it\n')
            FreeCAD.Console.PrintMessage('g...shift: grap element and move it slowly\n')
            FreeCAD.Console.PrintMessage('g...x: grap element and move it in x-direction\n')
            FreeCAD.Console.PrintMessage('g...y: grap element and move it in y-direction\n')
            FreeCAD.Console.PrintMessage('i...insert a new marker (point)\n')
            FreeCAD.Console.PrintMessage('cltr + i...attachment point (line-tool)\n')
            FreeCAD.Console.PrintMessage('del...delete a point or a line\n')
            FreeCAD.Console.PrintMessage('l...create line from 2 points (line-tool)\n')
            FreeCAD.Console.PrintMessage('cltr...multiselection\n')
            self.first_startup = True

    def Deactivated(self):
        pass

Gui.addWorkbench(GliderWorkbench())

