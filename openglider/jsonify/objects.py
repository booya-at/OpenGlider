import openglider.glider
import openglider.airfoil
import openglider.lines
import openglider.glider.ballooning
import openglider.glider.rib_elements

__ALL__ = ['objects']


def return_glider(ribs, cells, lineset=None):
    for cell in cells:
        if isinstance(cell.rib1, int):
            cell.rib1 = ribs[cell.rib1]
        if isinstance(cell.rib2, int):
            cell.rib2 = ribs[cell.rib2]
    # TODO: put rib-references into attachment points
    return openglider.glider.Glider(cells)


def return_lineset(lines, nodes, v_inf):
    for line in lines:
        if isinstance(line.upper_node, int):
            line.upper_node = nodes[line.upper_node]
        if isinstance(line.lower_node, int):
            line.lower_node = nodes[line.lower_node]
    return openglider.lines.LineSet(lines, v_inf)

objects = {"Glider": return_glider,
           "Rib": openglider.glider.Rib,
           "Cell": openglider.glider.Cell,
           "BallooningBezier": openglider.glider.ballooning.BallooningBezier,
           "Profile2D": openglider.airfoil.Profile2D,
           "LineSet": return_lineset,
           "Line": openglider.lines.Line,
           "Node": openglider.lines.Node,
           "AttachmentPoint": openglider.glider.rib_elements.AttachmentPoint}