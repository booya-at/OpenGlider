# glider tables

## Rib Table

### holes

- HOLE
  * length: 2
  * attributes: pos: Any, size: Any
- QUERLOCH
  * length: 2
  * attributes: pos: Any, size: Any
- HOLE5
  * length: 5
  * attributes: pos: Any, size: Any, width: Any, vertical_shift: Any, rotation: Any
- HOLESQ
  * length: 3
  * attributes: x: float, width: float, height: float
- HOLESQMULTI
  * length: 5
  * attributes: start: float, end: float, height: float, num_holes: int, border_width: float
- HOLESQMULTI6
  * length: 6
  * attributes: start: float, end: float, height: float, num_holes: int, border_width: float, margin: float
- HOLEATP
  * length: 4
  * attributes: start: float, end: float, height: float, num_holes: int
- HOLEATP6
  * length: 6
  * attributes: start: float, end: float, height: float, num_holes: int, border: float, side_border: float
- HOLEATP7
  * length: 7
  * attributes: start: float, end: float, height: float, num_holes: int, border: float, side_border: float, corner_size: float


### rigidfoils_rib

- RIGIDFOIL
  * length: 3
  * attributes: start: float, end: float, distance: float
- RIGIDFOIL3
  * length: 3
  * attributes: start: float, end: float, distance: float
- RIGIDFOIL5
  * length: 5
  * attributes: start: float, end: float, distance: float, circle_radius: float, circle_amount: float


### material_ribs

- MATERIAL
  * length: 1
  * attributes: Name: Any


### rib_modifiers

- SkinRib
  * length: 2
  * attributes: continued_min_end: float, xrot: float
- SkinRib7
  * length: 12
  * attributes: att_dist: float, height: float, continued_min: bool, continued_min_angle: float, continued_min_delta_y: float, continued_min_end: float, continued_min_x: float, double_first: bool, le_gap: bool, straight_te: bool, te_gap: bool, num_points: int
- XRot
  * length: 1
  * attributes: angle: float


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
  * length: 4
  * attributes: position: float, amount: float, start: float, end: float
- Sharknose8
  * length: 8
  * attributes: position: float, amount: float, start: float, end: float, angle_front: float, angle_back: float, rigidfoil_circle_radius: float, rigidfoil_circle_amount: float


### attachment_points_rib

- ATP
  * length: 3
  * attributes: name: str, pos: float, force: Union
- AHP
  * length: 3
  * attributes: name: str, pos: float, force: Union
- ATPPROTO
  * length: 4
  * attributes: name: str, pos: float, force: Union, proto_distance: float


## Cell Table

### cuts

- CUT_ROUND
  * length: 4
  * attributes: left: Any, right: Any, center: Any, amount: Any
- EKV
  * length: 2
  * attributes: left: Any, right: Any
- EKH
  * length: 2
  * attributes: left: Any, right: Any
- folded
  * length: 2
  * attributes: left: Any, right: Any
- DESIGNM
  * length: 2
  * attributes: left: Any, right: Any
- DESIGNO
  * length: 2
  * attributes: left: Any, right: Any
- orthogonal
  * length: 2
  * attributes: left: Any, right: Any
- CUT3D
  * length: 2
  * attributes: left: Any, right: Any
- cut_3d
  * length: 2
  * attributes: left: Any, right: Any
- singleskin
  * length: 2
  * attributes: left: Any, right: Any


### ballooning_factors

- BallooningFactor
  * length: 1
  * attributes: amount_factor: Any
- BallooningMerge
  * length: 1
  * attributes: merge_factor: Any


### diagonals

- QR
  * length: 6
  * attributes: left: Any, right: Any, width_left: Any, width_right: Any, height_left: Any, height_right: Any


### straps

- STRAP
  * length: 3
  * attributes: left: float, right: float, width: float
- VEKTLAENGE
  * length: 2
  * attributes: left: float, right: float


### rigidfoils_cell

- RIGIDFOIL
  * length: 3
  * attributes: x_start: float, x_end: float, y: float


### material_cells

- MATERIAL
  * length: 1
  * attributes: Name: Any


### miniribs

- MINIRIB
  * length: 2
  * attributes: yvalue: Any, front_cut: Any


### attachment_points_cell

- ATP
  * length: 4
  * attributes: name: str, cell_pos: float, rib_pos: float, force: Union
- ATPDIFF
  * length: 5
  * attributes: name: str, cell_pos: float, rib_pos: float, force: Union, offset: float
- AHP
  * length: 4
  * attributes: name: str, cell_pos: float, rib_pos: float, force: Union


## General Table

### curves



