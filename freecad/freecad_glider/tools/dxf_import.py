# a FreeCAD Library 

#***************************************************************************
#*   (c) Benjamin Alterauge (gift) 2018 - 2020                             *   
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import numpy as np
import FreeCAD, Part

GC_ENTITY_TYPE = 0
GC_HANDLE      = 5
GC_DOUBLE      = np.concatenate((np.arange(10,59),np.arange(140,147)))
GC_INT16       = np.concatenate((np.arange(60,79),np.arange(170,175),np.arange(400,409),np.arange(1060,1070)))
GC_INT32       = np.concatenate((np.arange(90,99),[1071]))
GC_X           = 10
GC_Y           = 20
GC_Z           = 30

class DXFEntity:

    def __init__(self, et=''): self.groupcodes = {GC_ENTITY_TYPE : et}
    def set(self, gc, vl):     self.groupcodes[gc] = vl
    def value(self, gc):       return self.groupcodes[gc]
    def type(self):            self.groupcodes[GC_ENTITY_TYPE]
    def handle(self):          self.groupcodes[GC_HANDLE]
    
    def set_list(self, gc, vl):
        if gc in self.groupcodes:
            self.groupcodes[gc].append(vl)
        else:
            self.groupcodes[gc] = [vl] 

class DXFPolyline(DXFEntity):
    def __init__(self, et='POLYLINE'): 
        self.vertexes = []
        DXFEntity.__init__(self, et)

    def add_vertex(self, obj):
        self.vertexes.append(obj)

    def get_vertexes(self):
        return self.vertexes

    def count_vertexes(self):
        return len(self.vertexes)

    def to_wire(self):
        import Part
        dw = Part.makePolygon([i.vector() for i in self.get_vertexes()])
        Part.show(dw)
        return dw

    def to_points(self):
        import Points
        pp=Points.Points()
        pp.addPoints([i.vector() for i in self.get_vertexes()])
        Points.show(pp)
        return pp

    def to_fc(self):
        return self.to_wire()

    def is_polyline(self):
        return True

class DXFVertex(DXFEntity):
    def __init__(self, et='VERTEX'):
        DXFEntity.__init__(self, et)
        self.set(GC_X, 0.0)
        self.set(GC_Y, 0.0)
        self.set(GC_Z, 0.0)

    def x(self): return self.value(GC_X)
    def y(self): return self.value(GC_Y)
    def z(self): return self.value(GC_Z)
    def vector(self): return FreeCAD.Vector(self.x(), self.y(), self.z())
    def is_vertex(): return True

class DXFLine(DXFEntity):
    def __init__(self, et='LINE'):
        DXFEntity.__init__(self, et)
        self.set(GC_X, 0.0)
        self.set(GC_Y, 0.0)
        self.set(GC_Z, 0.0)
        self.set(GC_X+1, 0.0)
        self.set(GC_Y+1, 0.0)
        self.set(GC_Z+1, 0.0)

    def x1(self): return self.value(GC_X)
    def y1(self): return self.value(GC_Y)
    def z1(self): return self.value(GC_Z)
    def x2(self): return self.value(GC_X+1)
    def y2(self): return self.value(GC_Y+1)
    def z2(self): return self.value(GC_Z+1)
    def is_line(self): return True
    def toEdge(self): return Part.makeLine((self.x1(), self.y1(), self.z1()), (self.x2(), self.y2(), self.z2()))

    
class DXFFACE(DXFEntity):
    def __init__(self, et='PLANE'):
        DXFEntity.__init__(self, et)
        self.set(GC_X, 0.0)
        self.set(GC_Y, 0.0)
        self.set(GC_Z, 0.0)
        self.set(GC_X+1, 0.0)
        self.set(GC_Y+1, 0.0)
        self.set(GC_Z+1, 0.0)
        self.set(GC_X+2, 0.0)
        self.set(GC_Y+2, 0.0)
        self.set(GC_Z+2, 0.0)
        self.set(GC_X+3, 0.0)
        self.set(GC_Y+3, 0.0)
        self.set(GC_Z+3, 0.0)

    def x1(self): return self.value(GC_X)
    def y1(self): return self.value(GC_Y)
    def z1(self): return self.value(GC_Z)
    def x2(self): return self.value(GC_X+1)
    def y2(self): return self.value(GC_Y+1)
    def z2(self): return self.value(GC_Z+1)
    def x3(self): return self.value(GC_X+2)
    def y3(self): return self.value(GC_Y+2)
    def z3(self): return self.value(GC_Z+2)
    def x4(self): return self.value(GC_X+3)
    def y4(self): return self.value(GC_Y+3)
    def z4(self): return self.value(GC_Z+3)
    def is_plane(true): return True

class DXFSpline(DXFEntity):
    def __init__(self, et='VERTEX'):
        DXFEntity.__init__(self, et)
        
    def flag(self): return self.value(70)
    def is_spline(self): return True
    def is_closed(self): return (self.value(70)<<1)
    def is_periodic(self): return (self.value(70)<<2)
    def is_rational(self): return (self.value(70)<<4)
    def is_planar(self): return (self.value(70)<<8)
    def is_linear(self): return (self.value(70)&16) > 0
    
    def to_polygon(self):
        import FreeCAD, Part
        poly = [] 
        for i in np.arange(len(self.value(GC_X))):
            poly.append(FreeCAD.Vector(self.value(GC_X)[i],self.value(GC_Y)[i],self.value(GC_Z)[i]))

        poly.pop(0)
        
        try:
            if (poly > 2):
                return Part.makePolygon(poly)
            elif (poly == 2):
                return Part.LineSegment(poly)
            else:
                return None
        except Part.OCCError:
            return None
        

def dublette(dxffile):
    code  = int(dxffile.readline())
    value = dxffile.readline().strip()
    if (code == GC_ENTITY_TYPE):
        value.upper()
    elif code in GC_INT16:
        value = np.int16(value)
    elif code in GC_INT32:
        value = np.int32(value)
    elif code in GC_DOUBLE:
        value = np.float64(value)  
    return [code, value]

def prase(filename):
    entries = { 'POLYLINE': 0, 'VERTEX': 0, 'LINE': 0, 'SPLINE': 0, '3DFACE':0 }
    result = []
    dxffile = open(filename,'r')
    while True:
        code, value = dublette(dxffile)
        if (value=='EOF'): break
        elif (value=='SECTION'):
            code, value = dublette(dxffile)
            if (value=='ENTITIES'): 
                polyline = None
                code, value = dublette(dxffile)
                while not (value=='ENDSEC'):
                    if (code==GC_ENTITY_TYPE):
                        support = 0
                        if (value=='POLYLINE'):
                            polyline = DXFPolyline()
                            result.append(polyline)
                            support = 1
                        elif (value=='VERTEX'):
                           if polyline:
                            result.append(DXFVertex())   
                            polyline.add_vertex(result[-1]) 
                            support = 1
                        elif (value=='3DFACE'):
                            result.append(DXFFACE())   
                            support = 1
                        elif (value=='SEQEND'):
                            if polyline:
                                polyline = None 
                        elif (value=='LINE'):
                            result.append(DXFLine()) 
                            support = 1
                        elif (value=='SPLINE'):
                            result.append(DXFSpline()) 
                            support = 2
                        if support>0:
                            entries[value] += 1
                    else:
                        if (support==1):
                            result[-1].set(code, value)
                        elif (support==2):
                            if code in [10,20,30,40]:
                                result[-1].set_list(code, value)
                            else:
                                result[-1].set(code, value)

                    code, value = dublette(dxffile)
    dxffile.close()
    return [entries, result]
