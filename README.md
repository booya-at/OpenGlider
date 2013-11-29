OpenGlider
==========

someday, hopefully this is open source paraglider design software


to try a simple cell setup, clone the repo:
  ```
  git clone https://github.com/hiaselhans/OpenGlider.git
  ```
link it to the python packages, install vtk and python2-scipy
then run the file

```
  python2 Test/testcell.py
```
use python2 as vtk is not yet available for p3.


Development Progress
====================

While still in an early status, here is a little screenshot to see the progress:

![screenshot testcell with miniribs][screen]

[screen]: Doc/screen.png


The plan is to build on:

* python ( http://docs.python.org/2/tutorial/ )
* vtk (visual toolkit, for 3d-output: http://www.vtk.org/)
* freecad (Open-Source Cad, written in c++ with python API (www.freecadweb.org/)
* include xfoil for 2D-foil calculation ( http://web.mit.edu/drela/Public/web/xfoil/ )
* use pyxfoil for xfoil integration(http://www.python-science.org/project/pyxfoil)
* for quick 3D-calculation use self-coded panelmethod (VSAERO) and/or apame implementation (http://www.3dpanelmethod.com/)
* export for OpenFoam (cfd, http://www.openfoam.com/)
* export for Code_Aster (fem, http://www.code-aster.org - maybe also calculix as we've done already, but it does currently not support membrane elements)

It will take some time, if you want to help, feel free to do so!
