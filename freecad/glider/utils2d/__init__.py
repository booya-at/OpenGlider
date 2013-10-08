import FreeCAD
import FreeCADGui
from FreeCAD import Vector



if FreeCAD.GuiUp:
    import FreeCADGui
    gui = True
else:
    print "FreeCAD Gui not present. Draft module will have some features disabled."
    gui = False

class _DraftObject:
    "The base class for Draft objects"
    def __init__(self,obj,tp="Unknown"):
        obj.Proxy = self
        self.Type = tp

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state

    def execute(self,obj):
        pass

    def onChanged(self, fp, prop):
        pass

class _ViewProviderDraft:
    "The base class for Draft Viewproviders"

    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj.Object

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def attach(self, obj):
        self.Object = obj.Object
        return

    def updateData(self, fp, prop):
        return

    def getDisplayModes(self,obj):
        modes=[]
        return modes

    def setDisplayMode(self,mode):
        return mode

    def onChanged(self, vp, prop):
        return

    def execute(self,obj):
        return

    def setEdit(self,vp,mode):
        FreeCADGui.runCommand("Draft_Edit")
        return True

    def unsetEdit(self,vp,mode):
        if FreeCAD.activeDraftCommand:
            FreeCAD.activeDraftCommand.finish()
        FreeCADGui.Control.closeDialog()
        return False

    def getIcon(self):
        return(":/icons/Draft_Draft.svg")

    def claimChildren(self):
        objs = []
        if hasattr(self.Object,"Base"):
            objs.append(self.Object.Base)
        if hasattr(self.Object,"Objects"):
            objs.extend(self.Object.Objects)
        if hasattr(self.Object,"Components"):
            objs.extend(self.Object.Components)
        return objs

class _Point(_DraftObject):
    "The Draft Point object"
    def __init__(self, obj,x,y,z):
        _DraftObject.__init__(self,obj,"Point")
        obj.addProperty("App::PropertyFloat","X","Point","Location").X = x
        obj.addProperty("App::PropertyFloat","Y","Point","Location").Y = y
        obj.addProperty("App::PropertyFloat","Z","Point","Location").Z = z
        mode = 2
        obj.setEditorMode('Placement',mode)

    def execute(self, fp):
        self.createGeometry(fp)

    def createGeometry(self,fp):
        import Part
        shape = Part.Vertex(Vector(fp.X,fp.Y,fp.Z))
        fp.Shape = shape


class _ViewProviderPoint(_ViewProviderDraft):
    "A viewprovider for the Draft Point object"
    def __init__(self, obj):
        _ViewProviderDraft.__init__(self,obj)

    def onChanged(self, vp, prop):
        mode = 2
        vp.setEditorMode('LineColor',mode)
        vp.setEditorMode('LineWidth',mode)
        vp.setEditorMode('BoundingBox',mode)
        vp.setEditorMode('ControlPoints',mode)
        vp.setEditorMode('Deviation',mode)
        vp.setEditorMode('DiffuseColor',mode)
        vp.setEditorMode('DisplayMode',mode)
        vp.setEditorMode('Lighting',mode)
        vp.setEditorMode('LineMaterial',mode)
        vp.setEditorMode('ShapeColor',mode)
        vp.setEditorMode('ShapeMaterial',mode)
        vp.setEditorMode('Transparency',mode)

    def getIcon(self):
        return '/usr/lib/freecad/Mod/glider/icons/glider_obj_point.svg'


def glidermakePoint(X=0, Y=0, Z=0,color=None,name = "Point", point_size= 5):
    ''' make a point (at coordinates x,y,z ,color(r,g,b),point_size)
        example usage:
        p1 = makePoint()
        p1.ViewObject.Visibility= False # make it invisible
        p1.ViewObject.Visibility= True  # make it visible
        p1 = makePoint(-1,0,0) #make a point at -1,0,0
        p1 = makePoint(1,0,0,(1,0,0)) # color = red
        p1.X = 1 #move it in x
        p1.ViewObject.PointColor =(0.0,0.0,1.0) #change the color-make sure values are floats
    '''
    obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _Point(obj,X,Y,Z)
    obj.X = X
    obj.Y = Y
    obj.Z = Z
    if gui:
        _ViewProviderPoint(obj.ViewObject)
        if not color:
            color = FreeCADGui.draftToolBar.getDefaultColor('ui')
        obj.ViewObject.PointColor = (float(color[0]), float(color[1]), float(color[2]))
        obj.ViewObject.PointSize = point_size
        obj.ViewObject.Visibility = True
    FreeCAD.ActiveDocument.recompute()
    return obj