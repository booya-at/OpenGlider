__version__ = "0.1.2"
from . import glider_commands

def show_lineset_points(glider, pattern=None):
	import Part
	import FreeCAD as App
	points = []
	for line in glider.lineset.lines:
		if not pattern or pattern in line.name:
			points += [tuple(line.upper_node.vec.tolist())]
			points += [tuple(line.lower_node.vec.tolist())]
	# delete duplicates
	points = list(set(points))
	vertices = []
	for point in points:
		# rotate the points to align with rotation of glider
		vertices += [Part.Vertex(point[1], -point[0], point[2])]
	compound = Part.Compound(vertices)
	Part.show(compound)
