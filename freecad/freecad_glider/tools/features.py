from ._glider import OGBaseObject, OGGliderVP

import os
import copy
import numpy as np
import FreeCAD as App
from openglider.airfoil.profile_2d import Profile2D
from openglider.glider.rib import SingleSkinRib, RibHole


class BaseFeature(OGBaseObject):
    def __init__(self, obj, parent):
        self.obj = obj
        obj.addProperty('App::PropertyLink', 'parent', 'not yet', 'docs')
        obj.parent = parent
        super(BaseFeature, self).__init__(obj)
        self.addProperties()

    def drawGlider(self, call_parent=True):
        if not self.obj.ViewObject.Visibility:
            self.obj.ViewObject.Proxy.recompute = True
            if call_parent:
                self.obj.parent.Proxy.drawGlider()
        else:
            self.obj.ViewObject.Proxy.recompute = True
            self.obj.ViewObject.Proxy.updateData()
            if call_parent:
                self.obj.parent.Proxy.drawGlider()

    def getGliderInstance(self):
        '''adds stuff and returns changed copy'''
        return copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())

    def getParametricGlider(self):
        '''returns top level parametric glider'''
        return self.obj.parent.Proxy.getParametricGlider()

    def setParametricGlider(self, obj):
        '''sets the top-level glider2d and recomputes the glider3d'''
        self.obj.parent.Proxy.setParametricGlider(obj)

    def getRoot(self):
        '''return the root freecad obj'''
        return self.obj.parent.Proxy.getRoot()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def execute(self, fp):
        self.drawGlider()

################# this function belongs to the gui and should be implemented in another way
    def onDocumentRestored(self, obj):
        if not hasattr(self, 'obj'):
            self.obj = obj
            if self.obj.parent.ViewObject.Visibility:
                self.obj.parent.ViewObject.Visibility = False
            self.obj.parent.Proxy.onDocumentRestored(self.obj.parent)

            if App.GuiUp and not self.obj.ViewObject.Proxy:
                self.restore_view_provider()  # defined in parent class
            # backward compatibility (remove this)
            self.obj.Proxy.addProperties()

            self.obj.ViewObject.Proxy.recompute = True
            # we have blocked the automatic update mechanism. so now we have to call it manually
            if self.obj.ViewObject.Visibility:
                print(self)
                print("updating the view")
                self.obj.ViewObject.Proxy.updateData(prop='Visibility')
#########################################################################################

class RibFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(RibFeature, self).__init__(obj, parent)

    def addProperties(self):
        self.obj.addProperty('App::PropertyIntegerList', 'ribs', 'not yet', 'docs')
        self.obj.addProperty('App::PropertyInteger', 'airfoil', 'not yet', 'docs')
        self.addProperty('rib_offset', 0., 'not yet', 'orthogonal offset of ribs relative to chord')
        self.addProperty('delta_aoa', 0., 'not yet', 'additional (delta) aoa')

    def getGliderInstance(self):
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())
        airfoil = self.obj.parent.Proxy.getParametricGlider().profiles[self.obj.airfoil]
        for i, rib in enumerate(glider.ribs):
            if i in self.obj.ribs:
                rib.profile_2d = airfoil
                rib.pos += rib.in_plane_normale * self.obj.rib_offset * rib.chord
                rib.aoa_absolute += self.obj.delta_aoa
        return glider

class VRibFeature(OGGliderVP):
    def getIcon(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        return(_dir + "/../icons/rib_feature.svg")


class BallooningFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(BallooningFeature, self).__init__(obj, parent)
        obj.addProperty('App::PropertyIntegerList', 'cells', 'not yet', 'docs')
        obj.addProperty('App::PropertyInteger', 'ballooning', 'not yet', 'docs')

    def getGliderInstance(self):
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())
        ballooning = self.obj.parent.Proxy.getParametricGlider().balloonings[self.obj.ballooning]
        for i, cell in enumerate(glider.cells):
            if i in self.obj.cells:
                cell.ballooning = ballooning
        return glider


class VBallooningFeature(OGGliderVP):
    def getIcon(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        return(_dir + "/../icons/ballooning_feature.svg")


class SharkFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(SharkFeature, self).__init__(obj, parent)

    def addProperties(self):
        self.addProperty('ribs', [], 'not_yet', 'docs', int)
        self.addProperty('x1', 0.1, 'not_yet', 'distance')
        self.addProperty('x2', 0.11, 'not_yet', 'distance')
        self.addProperty('x3', 0.5, 'not_yet', 'distance')
        self.addProperty('y_add', 0.1, 'not_yet', 'amount')
        self.addProperty('type', False, 'not_yet', '0-> linear, 1->quadratic')

    def apply(self, airfoil_data, x1, x2, x3, y_add):
        data = []
        for x, y in copy.copy(airfoil_data):
            if y < 0:
                if x > x1 and x < x2:
                    y -= y_add * (x - x1) / (x2 - x1)  # here any function
                elif x > x2 and x < x3:
                    y -= y_add * (x3 - x) / (x3 - x2)  # here another function
            data.append([x, y])
        return np.array(data)

    def getGliderInstance(self):
        x1, x2, x3, y_add =  self.obj.x1, self.obj.x2, self.obj.x3, self.obj.y_add
        from openglider.airfoil.profile_2d import Profile2D
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())
        for rib in enumerate(glider.ribs):
            rib.profile_2d = Profile2D(self.apply(rib.profile_2d._data, x1, x2, x3, y_add))
        return glider


class VSharkFeature(OGGliderVP):
    def getIcon(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        return(_dir + "/../icons/shark_feature.svg")


class SingleSkinRibFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(SingleSkinRibFeature, self).__init__(obj, parent)
        obj.addProperty('App::PropertyIntegerList',
                        'ribs', 'not yet', 'docs')
        self.addProperties()

    def getGliderInstance(self):
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())
        new_ribs = []
        self.addProperties()

        single_skin_par = {'att_dist': self.obj.att_dist,
                           'height': self.obj.height,
                           'num_points': self.obj.num_points,
                           'le_gap': self.obj.le_gap,
                           'te_gap': self.obj.te_gap,
                           'double_first': self.obj.double_first,
                           'straight_te': self.obj.straight_te,
                           'continued_min': self.obj.continued_min,
                           'continued_min_end': self.obj.continued_min_end,
                           'continued_min_angle': self.obj.continued_min_angle,
                           'continued_min_delta_y': self.obj.continued_min_delta_y,
                           'continued_min_x': self.obj.continued_min_x}

        for i, rib in enumerate(glider.ribs):
            if i in self.obj.ribs:
                if not isinstance(rib, SingleSkinRib):
                    new_ribs.append(SingleSkinRib.from_rib(rib, single_skin_par))
                else:
                    rib.single_skin_par = single_skin_par
                    new_ribs.append(rib)
            else:
                new_ribs.append(rib)
        for rib, ss_rib in zip(glider.ribs, new_ribs):
            if hasattr(rib, 'mirrored_rib') and rib.mirrored_rib:
                nr = glider.ribs.index(rib.mirrored_rib)
                ss_rib.mirrored_rib = new_ribs[nr]
        glider.replace_ribs(new_ribs)
        hole_size = np.array([self.obj.hole_width, self.obj.hole_height])
        if self.obj.holes:
            for att_pnt in glider.lineset.attachment_points:
                if (isinstance(att_pnt.rib, SingleSkinRib) and 
                    att_pnt.rib_pos > self.obj.min_hole_pos and
                    att_pnt.rib_pos < self.obj.max_hole_pos):
                    att_pnt.rib.holes.append(RibHole(att_pnt.rib_pos,
                                                     size=hole_size,
                                                     horizontal_shift=self.obj.horizontal_shift))
        for i, rib in enumerate(glider.ribs):
            rib.xrot = self.obj.xrot[i]

        return glider

    def addProperties(self):
        self.addProperty('height', 0.5, 'bows', 'docs')
        self.addProperty('att_dist', 0.1, 'bows', 'docs')
        self.addProperty('num_points', 20, 'bows', 'number of points')
        self.addProperty('le_gap', True, 'bows', 'should the leading edge match the rib')
        self.addProperty('te_gap', True, 'bows', 'should the trailing edge match the rib')
        self.addProperty('straight_te', True, 'bows', 'straight last bow')
        self.addProperty('double_first', False, 'bows', 'this is for double a lines')
        self.addProperty('holes', False, 'hole', 'create holes in the rib')
        self.addProperty('hole_height', 0.7, 'hole', 'height of ellipse')
        self.addProperty('hole_width', 0.3, 'hole', 'width of ellipse')
        self.addProperty('max_hole_pos', 1., 'hole', 'maximal relative position of hole')
        self.addProperty('horizontal_shift', 0.2, 'hole', 'relative horizontal shift')
        self.addProperty('min_hole_pos', 0.2, 'hole', 'minimal relative position of hole')
        self.addProperty('continued_min', False, 'bows', 'add an offset to the airfoil')
        self.addProperty('continued_min_end', 0.9, 'bows', 'no idea')
        self.addProperty('continued_min_angle', 0., 'bows', 'no idea')
        self.addProperty('continued_min_delta_y', 0., 'bows', 'no idea')
        self.addProperty('continued_min_x', 0., 'bows', 'no idea')
        glider = self.obj.parent.Proxy.getGliderInstance()
        angle_list = [0. for _ in glider.ribs]
        self.addProperty('xrot', angle_list, 'not_yet', 'set rib angles')


class VSingleSkinRibFeature(OGGliderVP):
    def getIcon(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        return(_dir + "/../icons/singleskin_feature.svg")


class FlapFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(FlapFeature, self).__init__(obj, parent)

    def addProperties(self):
        self.addProperty('flap_begin', 0.95, 'flap', 'where should the flapping effect start', float)
        self.addProperty('flap_amount', 0.01, 'flap', 'how much flapping', float)
        self.addProperty('flap_ribs', [], 'flap', 'which ribs get flapped', int)

    def getGliderInstance(self):
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())
        new_ribs = []
        self.addProperties()

        for i, rib in enumerate(glider.ribs):
            if i in self.obj.flap_ribs:
                rib.profile_2d.set_flap(self.obj.flap_begin, self.obj.flap_amount)
        return glider


class VFlapFeature(OGGliderVP):
    def getIcon(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        return(_dir + "/../icons/flap_feature.svg")


class HoleFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(HoleFeature, self).__init__(obj, parent)

    def getGliderInstance(self):
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())

        ribs = [rib for i, rib in enumerate(glider.ribs) if i in self.obj.ribs]
        new_ribs = []
        self.addProperties()

        hole_size = np.array([self.obj.hole_width, self.obj.hole_height])
        if self.obj.holes:
            for i, att_pnt in enumerate(glider.lineset.attachment_points):
                if (att_pnt.rib in ribs and 
                    att_pnt.rib_pos > self.obj.min_hole_pos and
                    att_pnt.rib_pos < self.obj.max_hole_pos):
                    att_pnt.rib.holes.append(RibHole(att_pnt.rib_pos,
                                                     size=hole_size,
                                                     horizontal_shift=self.obj.horizontal_shift,
                                                     rotation=self.obj.rotation))

        return glider

    def addProperties(self):
        self.addProperty('ribs', [], 'hole', 'docs', int)
        self.addProperty('holes', False, 'hole', 'create holes in the rib')
        self.addProperty('hole_height', 0.7, 'hole', 'height of ellipse')
        self.addProperty('hole_width', 0.3, 'hole', 'width of ellipse')
        self.addProperty('max_hole_pos', 1., 'hole', 'maximal relative position of hole')
        self.addProperty('horizontal_shift', 0.2, 'hole', 'relative horizontal shift')
        self.addProperty('min_hole_pos', 0.2, 'hole', 'minimal relative position of hole')
        self.addProperty('rotation', 0.0, 'hole', 'docs')


class VHoleFeature(OGGliderVP):
    def getIcon(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        return(_dir + "/../icons/hole_feature.svg")


class ScaleFeature(BaseFeature):
    def __init__(self, obj, parent):
        super(ScaleFeature, self).__init__(obj, parent)

    def addProperties(self):
        self.addProperty('scale', 1.0, 'scale', 'scales the glider')

    def getGliderInstance(self):
        glider = copy.deepcopy(self.obj.parent.Proxy.getGliderInstance())
        glider.scale(self.obj.scale)
        return glider