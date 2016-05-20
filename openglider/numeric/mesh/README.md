Mesh
====

A generic Mesh object to build connectivity information for visualiziation and simulation.

## functionality and members
 - nodes  
    ? really necessary?  
    all points that are used in the mesh.

 - polygons  
    all surfaces or lines.

 - edges
    {name: point_list}

 - clean_nodes()  
    remove duplicate points and

 - mesh1 + mesh2  
    add two mesh object, by merginging the nodes and recreating the conectivity information.


```python
from openglider import mesh
.
.
.

cell_mesh = cell.getMesh()
diagonal_mesh = diagonal.getMesh()
rib_mesh = rib.getMesh()


```
