# glider tables

## Rib Table

### holes

- HOLE
  1: pos  (Percentage)
  2: size  (Percentage)

- QUERLOCH
  1: pos  (Percentage)
  2: size  (Percentage)

- HOLESQ
  1: x  (Percentage)
  2: width  (Percentage)
  3: height  (Percentage)

- HOLE5
  1: pos  (Percentage)
  2: size  (Percentage)
  3: width  (Percentage)
  4: vertical_shift  (Percentage)
  5: rotation  (Angle)

- HOLESQMULTI
  1: start  (Percentage)
  2: end  (Percentage)
  3: height  (Percentage)
  4: num_holes  (int)
  5: border_width  (Percentage | Length)

- HOLESQMULTI6
  1: start  (Percentage)
  2: end  (Percentage)
  3: height  (Percentage)
  4: num_holes  (int)
  5: border_width  (Percentage | Length)
  6: margin  (Percentage | Length)

- HOLEATP
  1: start  (Percentage)
  2: end  (Percentage)
  3: num_holes  (int)

- HOLEATP5
  1: start  (Percentage)
  2: end  (Percentage)
  3: num_holes  (int)
  4: border  (Length | Percentage)
  5: side_border  (Length | Percentage)

- HOLEATP6
  1: start  (Percentage)
  2: end  (Percentage)
  3: num_holes  (int)
  4: border  (Length | Percentage)
  5: side_border  (Length | Percentage)
  6: corner_size  (Percentage)



### rigidfoils_rib

- RIGIDFOIL
  1: start  (Percentage)
  2: end  (Percentage)
  3: distance  (Length)

- RIGIDFOIL3
  1: start  (Percentage)
  2: end  (Percentage)
  3: distance  (Length)

- RIGIDFOIL5
  1: start  (Percentage)
  2: end  (Percentage)
  3: distance  (Length)
  4: circle_radius  (Length)
  5: circle_amount  (Percentage)



### material_ribs

- MATERIAL
  * length: 1
  * attributes: Name: str


### rib_modifiers

- SkinRib7
  * length: 12
  * attributes: att_dist: float, height: float, continued_min: bool, continued_min_angle: float, continued_min_delta_y: float, continued_min_end: float, continued_min_x: float, double_first: bool, le_gap: bool, straight_te: bool, te_gap: bool, num_points: int
- XRot
  * length: 1
  * attributes: angle: float
- SkinRib
  1: continued_min_end  (Percentage)
  2: xrot  (Angle)



### profiles

- ProfileFactor
  * length: 1
  * attributes: thickness_factor: Any
- ProfileMerge
  * length: 1
  * attributes: merge_factor: Any
- Flap
  * length: 2
  * attributes: begin: Any, amount: Any
- Sharknose
  1: position  (Percentage)
  2: amount  (Percentage)
  3: start  (Percentage)
  4: end  (Percentage)

- Sharknose8
  1: position  (Percentage)
  2: amount  (Percentage)
  3: start  (Percentage)
  4: end  (Percentage)
  5: angle_front  (Angle)
  6: angle_back  (Angle)
  7: rigidfoil_circle_radius  (Length)
  8: rigidfoil_circle_amount  (Length)



### attachment_points_rib

- AHP
  * length: 3
  * attributes: name: str, pos: float, force: Union
- ATP
  1: name  (str)
  2: rib_pos  (Percentage)
  3: force  (float | Vector3D)

- ATPPROTO
  1: name  (str)
  2: rib_pos  (Percentage)
  3: force  (float | Vector3D)
  4: protoloop_distance  (Percentage | Length)

- ATPPROTO5
  1: name  (str)
  2: rib_pos  (Percentage)
  3: force  (float | Vector3D)
  4: protoloop_distance  (Percentage | Length)
  5: protoloops  (int)



## Cell Table

### cuts

- DESIGNM
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- DESIGNO
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- orthogonal
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- EKV
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- EKH
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- folded
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- CUT3D
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- cut_3d
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)

- singleskin
  1: x (1)  (Percentage)
  2: x (2)  (Percentage)



### ballooning_factors

- BallooningFactor
  * length: 1
  * attributes: amount_factor: Any
- BallooningMerge
  * length: 1
  * attributes: merge_factor: Any
- BallooningRamp
  * length: 1
  * attributes: ballooning_ramp: Any


### diagonals

- QR
  1: position (1)  (Percentage)
  2: position (2)  (Percentage)
  3: width (1)  (Percentage | Length)
  4: width (2)  (Percentage | Length)
  5: height (1)  (Percentage)
  6: height (2)  (Percentage)

- DIAGONAL
  1: position (1)  (Percentage)
  2: position (2)  (Percentage)
  3: width (1)  (Percentage | Length)
  4: width (2)  (Percentage | Length)
  5: height (1)  (Percentage)
  6: height (2)  (Percentage)
  7: material_code  (str)



### straps

- STRAP
  1: position (1)  (Percentage)
  2: position (2)  (Percentage)
  3: width  (Percentage | Length)

- STRAP3
  1: position (1)  (Percentage)
  2: position (2)  (Percentage)
  3: width  (Percentage | Length)
  4: num_folds  (int)

- VEKTLAENGE
  1: position (1)  (Percentage)
  2: position (2)  (Percentage)



### rigidfoils_cell

- RIGIDFOIL
  * length: 3
  * attributes: x_start: Any, x_end: Any, y: Any


### material_cells

- MATERIAL
  * length: 1
  * attributes: Name: str


### miniribs

- MINIRIB
  1: y_value  (Percentage)
  2: front_cut  (Percentage)



### attachment_points_cell

- ATP
  * length: 4
  * attributes: name: str, cell_pos: float, rib_pos: float, force: Union
- AHP
  * length: 4
  * attributes: name: str, cell_pos: float, rib_pos: float, force: Union
- ATPDIFF
  * length: 5
  * attributes: name: str, cell_pos: float, rib_pos: float, force: Union, offset: float


## General Table

