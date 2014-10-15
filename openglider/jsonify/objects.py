import openglider.glider
import openglider.airfoil
import openglider.lines
import openglider.glider.ballooning
import openglider.glider.rib_elements

__ALL__ = ['objects']

objects = {"Glider": openglider.glider.Glider,
           "Glider_2D": openglider.glider.Glider_2D,
           "Rib": openglider.glider.Rib,
           "Cell": openglider.glider.Cell,
           "BallooningBezier": openglider.glider.ballooning.BallooningBezier,
           "Profile2D": openglider.airfoil.Profile2D,
           "LineSet": openglider.lines.LineSet,
           "Line": openglider.lines.Line,
           "Node": openglider.lines.Node,
           "AttachmentPoint": openglider.glider.rib_elements.AttachmentPoint}