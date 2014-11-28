import openglider.glider
import openglider.airfoil
import openglider.lines
import openglider.glider.ballooning
import openglider.glider.rib_elements

__ALL__ = ['objects']

objects = {"Glider": openglider.glider.Glider,
           "Rib": openglider.glider.Rib,
           "Cell": openglider.glider.Cell,
           "BallooningBezier": openglider.glider.ballooning.BallooningBezier,
           "Profile2D": openglider.airfoil.Profile2D,
           "LineSet": openglider.lines.LineSet,
           "Line": openglider.lines.Line,
           "Node": openglider.lines.Node,
           "AttachmentPoint": openglider.glider.rib_elements.AttachmentPoint,
           ################################BEZIER##############################
           "BezierCurve": openglider.utils.bezier.BezierCurve,
           "SymmetricBezier": openglider.utils.bezier.SymmetricBezier,
           ################################Glider2D############################
           "Glider_2D": openglider.glider.Glider_2D,
           "lw_att_point": openglider.glider.glider_2d.lw_att_point,
           "up_att_point": openglider.glider.glider_2d.up_att_point,
           "batch_point": openglider.glider.glider_2d.batch_point,
           "_lineset": openglider.glider.glider_2d._lineset,
           "_line": openglider.glider.glider_2d._line,
           }