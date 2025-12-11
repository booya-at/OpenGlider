# Better line-modul:


## Use truss elements to relax line stresses

The current computation of the lines has some assumptions which leads to geometry which doesn't fulfill the force equilibrium. To get a more exact solution for the line-problem we need to add a FEM step:

TODO:
- add implicit truss elements (paraFEM)
- create implicit solver (paraFEM)
- check availability of paraFEM in OpenGlider
- create a checkable member in the line computation (relax_stresses=False)
- make this consistent with the sag calculation
- test iterative approach to get line-length
