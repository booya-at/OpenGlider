# glider tables

## Rib Table

### holes

- HOLE
  * length: 2
  * attributes: ['pos', 'size'] 
- QUERLOCH
  * length: 2
  * attributes: ['pos', 'size'] 
- HOLE5
  * length: 5
  * attributes: ['pos', 'size', 'width', 'vertical_shift', 'rotation'] 
- HOLESQ
  * length: 3
  * attributes: ['x', 'width', 'height'] 
- HOLESQMULTI
  * length: 5
  * attributes: ['start', 'end', 'height', 'num_holes', 'border_width'] 


### rigidfoils_rib

- RIGIDFOIL
  * length: 3
  * attributes: ['start', 'end', 'distance'] 


### material_ribs

- MATERIAL
  * length: 1
  * attributes: ['Name'] 


### rib_modifiers

- SkinRib
  * length: 2
  * attributes: ['continued_min_end', 'xrot'] 
- SkinRib7
  * length: 12
  * attributes: ['att_dist', 'height', 'continued_min', 'continued_min_angle', 'continued_min_delta_y', 'continued_min_end', 'continued_min_x', 'double_first', 'le_gap', 'straight_te', 'te_gap', 'num_points'] 
- XRot
  * length: 1
  * attributes: ['angle'] 


### profiles

- ProfileFactor
  * length: 1
  * attributes: ['thickness_factor'] 
- ProfileMerge
  * length: 1
  * attributes: ['merge_factor'] 
- Flap
  * length: 2
  * attributes: ['begin', 'amount'] 


### attachment_points_rib

- ATP
  * length: 3
  * attributes: ['name', 'pos', 'force'] 
- AHP
  * length: 3
  * attributes: ['name', 'pos', 'force'] 
- ATPPROTO
  * length: 4
  * attributes: ['name', 'pos', 'force', 'proto_distance'] 


## Cell Table

### cuts

- CUT_ROUND
  * length: 4
  * attributes: ['left', 'right', 'center', 'amount'] 
- EKV
  * length: 2
  * attributes: ['left', 'right'] 
- EKH
  * length: 2
  * attributes: ['left', 'right'] 
- folded
  * length: 2
  * attributes: ['left', 'right'] 
- DESIGNM
  * length: 2
  * attributes: ['left', 'right'] 
- DESIGNO
  * length: 2
  * attributes: ['left', 'right'] 
- orthogonal
  * length: 2
  * attributes: ['left', 'right'] 
- CUT3D
  * length: 2
  * attributes: ['left', 'right'] 
- cut_3d
  * length: 2
  * attributes: ['left', 'right'] 
- singleskin
  * length: 2
  * attributes: ['left', 'right'] 


### ballooning_factors

- BallooningFactor
  * length: 1
  * attributes: ['amount_factor'] 
- BallooningMerge
  * length: 1
  * attributes: ['merge_factor'] 


### diagonals

- QR
  * length: 6
  * attributes: ['left', 'right', 'width_left', 'width_right', 'height_left', 'height_right'] 


### straps

- STRAP
  * length: 3
  * attributes: ['left', 'right', 'width'] 
- VEKTLAENGE
  * length: 2
  * attributes: ['left', 'right'] 


### rigidfoils_cell

- RIGIDFOIL
  * length: 3
  * attributes: ['x_start', 'x_end', 'y'] 


### material_cells

- MATERIAL
  * length: 1
  * attributes: ['Name'] 


### miniribs

- MINIRIB
  * length: 2
  * attributes: ['yvalue', 'front_cut'] 


### attachment_points_cell

- ATP
  * length: 4
  * attributes: ['name', 'cell_pos', 'rib_pos', 'force'] 
- ATPDIFF
  * length: 5
  * attributes: ['name', 'cell_pos', 'rib_pos', 'force', 'offset'] 
- AHP
  * length: 4
  * attributes: ['name', 'cell_pos', 'rib_pos', 'force'] 


## General Table

