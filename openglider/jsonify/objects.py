import openglider.airfoil
import openglider.lines
from openglider.vector.spline import BezierCurve, SymmetricBezier
import openglider.glider
import openglider.glider.ballooning
import openglider.glider.rib
import openglider.glider.cell
import openglider.glider.glider_2d

__ALL__ = ['objects']

objects = {"Glider": openglider.glider.Glider,
           "Rib": openglider.glider.rib.Rib,
           "Cell": openglider.glider.cell.Cell,
           "BallooningBezier": openglider.glider.ballooning.BallooningBezier,
           "Profile2D": openglider.airfoil.Profile2D,
           "BezierProfile2D": openglider.airfoil.BezierProfile2D,
           "LineSet": openglider.lines.LineSet,
           "Line": openglider.lines.Line,
           "Node": openglider.lines.Node,
           "AttachmentPoint": openglider.glider.rib.AttachmentPoint,
           ################################BEZIER##############################
           "BezierCurve": BezierCurve,
           "SymmetricBezier": SymmetricBezier,
           ################################Glider2D############################
           "Glider2D": openglider.glider.Glider2D,
           "LineSet2D": openglider.glider.glider_2d.LineSet2D,
           "LowerNode2D": openglider.glider.glider_2d.LowerNode2D,
           "UpperNode2D": openglider.glider.glider_2d.UpperNode2D,
           "BatchNode2D": openglider.glider.glider_2d.BatchNode2D,
           "Line2D": openglider.glider.glider_2d.Line2D,
           "Panel": openglider.glider.cell.Panel
           }