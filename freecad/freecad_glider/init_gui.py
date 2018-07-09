import os
try:
    import FreeCADGui as Gui
    import FreeCAD
except ImportError:
    print('module not loaded with freecad')


from pivy import coin

# as long as this isn't part of std pivy:
########################################################################################
def SoGroup__iadd__(self, other):
    if isinstance(other, (list, tuple)):
        for other_i in other:
            self.__iadd__(other_i)
        return self
    else:
        try:
            self.addChild(other)
            return self
        except TypeError as e:
            raise TypeError(str(self.__class__) + " accepts only objects of type pivy.coin.SoNode")

def SoGroup__isub__(self, other):
    if isinstance(other, (list, tuple)):
        for other_i in other:
            self.__isub__(other_i)
        return self
    else:
        try:
            self.removeChild(other)
            return self
        except TypeError as e:
            raise TypeError(str(self.__class__) + " can't remove child of type " + str(type(other)))


def SoGroup_getByName(self, name):
    for child in self:
        if name == child.getName():
            return child
    return None


coin.SoGroup.__iadd__ = SoGroup__iadd__
coin.SoGroup.__isub__ = SoGroup__isub__
coin.SoGroup.getByName = SoGroup_getByName
########################################################################################

Dir = os.path.abspath(os.path.dirname(__file__))
Gui.addIconPath(os.path.join(Dir, 'icons'))


class gliderWorkbench(Gui.Workbench):
    MenuText = 'glider'
    ToolTip = 'glider workbench'
    Icon = 'glider_workbench.svg'
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
        'GliderScaleFeatureCommand']

    productionBox = [
        'PatternCommand',
        'PanelCommand',
        'PolarsCommand']

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


        Gui.addPreferencePage(Dir + '/ui/preferences.ui', 'Display')

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(gliderWorkbench())