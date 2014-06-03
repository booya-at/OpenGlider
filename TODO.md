TODO:
==========

¡Hola!
This is a short todo list//Roadmap
If you have spare time, be productive!


Classes
-------

- [] Xfoil integration for Profiles (XFLR5-API??)
- [] Cells -> seperate midpoint from midrib, diagonals,..
- [] 4-/5-cell diagonals,
    - [] form: x^2 function (reverse line-blowout: |\_/| )
    - [] cut with central rib
    - [] 2 common diagonals as a function return
-miniribs -> sin-function
-sharknose
    - [] 2 sticks
    - [] modify airfoil


Exports
-------

- [] Calculix Export
- [] (Apame Export)
- [] ods-geometry-export
- [] gmsh vortexje

Imports
-------

- [] If you have your own input format -> write a import function
- [] apame results
- [] json panelmethod results
- [] vtk vortexje
- [] Make JSON-Inputfile, write import+export containing:
    - [] basic geometry being either spline-data OR! explicit values:
        - [] rib-data
            - [] x/y
            - [] aoa (direct/indirect)
            - [] profile-merge
            - [] balloon-merge
            - [] holes, attachment-points, 
        - [] cell-data (x/y, aoa,...)
            - [] cuts/parts
            - [] diagonals/tensionstraps
            - [] midribs
            - [] 
    - [] profiles
    - [] balloonings (spline-points x/y)
    - [] lineset
        - [] lower points (pilot)
        - [] lines (nested lists?)
    - [] sewing-properties
        - [] allowances
        - [] marks


Flattening
----------

- [] Flatten-panels: add sewing-position-marks, attachmentpoint-marks,..
- [] Flatten-profiles: add entry, add holes
- [] Flatten-diagonals
- [] Markings -> text (vector-text)

Input
-----

- [] Create dragable spline-curves
- [] Wizards for shape, AOA , curvature,... (with matplotlib)
- [] (choose between Blender, FreeCAD)

Panelmethod
-----------

- [] Write json import/export
- [] check results
- [] provide sample file + test
