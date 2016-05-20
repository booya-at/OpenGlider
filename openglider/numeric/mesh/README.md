# mesh

A generic Mesh object to build connectivity information for visualiziation and simulation.

### example

```python
from openglider.numeric.mesh import Vertex, Mesh

# create some vertices
p1 = Vertex(0, 0, 0)
p2 = Vertex(1, 0, 0)
p3 = Vertex(0, 1, 0)
p4 = Vertex(1, 1, 0)
p5 = Vertex(0, 0, 0)

# polygons are simple lists
a = [p1,p2,p3,p4]
b = [p1,p2,p4,p5]

# the mesh object is constructed with a
# polygon dict: {"poly_group": polygon_list}
# boundary_dict: {boundary_name: vertices list}
m1 = Mesh({"a": [a]}, boundary_nodes={"j": a})
m2 = Mesh({"b": [b]}, boundary_nodes={"j": b})

# join two meshes
m3 = m1 + m2

# delete all duplicate points
m3.delete_duplicates()

# get a indexed representation ready for other formats
vertices, polygons, boundaries = m3.get_indexed()

```

### get the mesh from the glider

```python
mesh = glider.get_mesh(numpoints)

```
