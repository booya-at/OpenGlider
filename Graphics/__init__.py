import vtk
from Vector import Depth

class GraphicsObject(object):
    """Creates a GraphicsObject"""
    def __init__(self,colour='black',typ='point',coordinates=[[0,0,0]]):
        self.colour=colour
        self.typ=typ
        self.coordinates=coordinates

    def _SetCoordinates(self,coordinates):
        self.coordinates=coordinates
        
    def _SetColour(self,colour):
        self.colour=colour
        
    def _SetTyp(self,typ):
        self.typ=typ
        
class Line(GraphicsObject):
    def __init__(self,coordinates=[[0,0,0],[1,1,1]],colour='black'):
        GraphicsObject.coordinates=coordinates
        GraphicsObject.typ='line'
        GraphicsObject.colour=colour
        

    
        
        
