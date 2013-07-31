import vtk
from Vector import Depth,Type


class GraphicObject(object):
    def __init__(self, pointnumbers,gtype):
        self.pointnumbers=pointnumbers
        self.type=gtype
        
class Point(GraphicObject):
    def __init__(self,pointnumbers):
        self.pointnumbers=pointnumbers
        self.type='Point'
        
class Line(GraphicObject):
    def __init__(self,pointnumbers):
        self.pointnumbers=pointnumbers
        self.type='Line'
        
class Polygon(GraphicObject):
    def __init__(self,pointnumbers):
        self.pointnumbers=pointnumbers
        self.type='Polygon'

def Graphics3D(coordinates, graphicsobject):
    Graphics(coordinates, graphicsobject,rotation=True)
    
def Graphics2D(coordinates, graphicsobject):
    Graphics(coordinates, graphicsobject,rotation=False)
    
class Graphics(object):
    """Creates a GraphicsObject"""
    def __init__(self,coordinates, graphicobjects,rotation=True):
        self.rotation=rotation
        self.coordinates=coordinates
        self.graphicobjects=graphicobjects
        
        self.points=vtk.vtkPoints()
        for coor in coordinates:
            self.points.InsertNextPoint(coor)
            
        self.lines = vtk.vtkCellArray()
        self.verts = vtk.vtkCellArray()
        self.polygons = vtk.vtkCellArray()
        
       
        for graphicobject in self.graphicobjects:
            if graphicobject.type == 'Line':
                self._createline(graphicobject.pointnumbers)
            elif graphicobject.type == 'Point':
                self._createpoint(graphicobject.pointnumbers)
            elif graphicobject.type == 'Polygon':
                self._createpolygon(graphicobject.pointnumbers)
       
        self.polydata = vtk.vtkPolyData()
        self.polydata.SetPoints(self.points)
        
        self.polydata.SetLines(self.lines)
        self.polydata.SetVerts(self.verts)
        self.polydata.SetPolys(self.polygons)
        
        self.mapper=vtk.vtkPolyDataMapper()
        self.mapper.SetInput(self.polydata)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self._createwindow()
     
    def _createpoint(self, pointnumbers):
        if Depth(pointnumbers)>=3:
            for p in pointnumbers:
                self._createpoint(p)
        else:
            self.verts.InsertNextCell(len(pointnumbers))
            for p in pointnumbers:                
                self.verts.InsertCellPoint(p)
  
    def _createline(self, pointnumbers):
        if Depth(pointnumbers)>=3:
            for p in pointnumbers:
                self._createline(p)
        else:
            for i in range(len(pointnumbers)-1):
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0,pointnumbers[i])
                line.GetPointIds().SetId(1,pointnumbers[i+1])
                self.lines.InsertNextCell(line)
                i=i+1
            
    def _createpolygon(self, pointnumbers):
        if Depth(pointnumbers)>=3:
            for p in pointnumbers:
                self._createpolygon(p)
        else:
            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(len(pointnumbers))
            i=0
            for p in pointnumbers:
                polygon.GetPointIds().SetId(i, p)
                i=i+1
            self.polygons.InsertNextCell(polygon)
        
    def _createwindow(self):
        ren1 = vtk.vtkRenderer()
        ren1.AddActor(self.actor)
        ren1.SetBackground(0.1, 0.2, 0.4)
        ren1.ResetCamera()
        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(ren1)
        renWin.SetSize(700, 700)
        iren = vtk.vtkRenderWindowInteractor()
        if self.rotation:
            iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        else:
            iren.SetInteractorStyle(vtk.vtkInteractorStyleRubberBand2D())
        iren.SetRenderWindow(renWin)
        iren.Initialize()
        iren.Start()
