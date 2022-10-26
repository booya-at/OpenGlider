# OpenGlider (airG fork)

This is the airG fork of OpenGlider.


## Try It


Clone the git-repo first:
```bash
git clone https://github.com/hiaselhans/OpenGlider.git
```

### Install with pip

```bash
cd OpenGlider
pip install -e .
```


## Documentation

Every module inside openglider *should* have a README where the functionality is documented.  
Please have a look at the [base module](./openglider/README.md).

### Unittests and Visual Tests

To run all unittests, run this from the main directory:
```bash
./testall.py
```

Or use `-a` flag to also run visual tests
```bash
./testall.py -a
```

## Used Tech

OpenGlider is built on top of these technologies:

* **Python** ([link](http://docs.python.org/3/tutorial/))

* **[]

* **[VTK](https://www.vtk.org/)** - visual toolkit for 3d-output

* ~~Code_Aster FEM export (http://www.code-aster.org) - maybe calculix as we've done already, but it does currently not support membrane elements)~~

* ~~xfoil//Pyxfoil for 2D-foil calculation (http://web.mit.edu/drela/Public/web/xfoil/) (http://www.python-science.org/project/pyxfoil)~~

It will take some time, if you want to help, feel free to do so!

Using some older code, we already created a few prototypes which can be seen on http://www.booya.at
