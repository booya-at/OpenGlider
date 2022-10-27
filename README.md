# OpenGlider (airG fork)

This is the airG fork of OpenGlider.

## Main differences to OpenGlider:

- without the freecad gui & dependencies
- excessive use of Pydantic Models for Physical objects (ribs, cells, panels, etc)
- added a custom qt-gui with compare functionality but no editing features.
- reduced the use of numpy and use [euklid](https://github.com/airgproducts/euklid) for vector calculations.

## Try It


Clone the git-repo first:
```bash
git clone https://github.com/airgproducts/openglider
```

### Install with pip

```bash
cd openglider
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

- **Python** ([link](http://docs.python.org/3/tutorial/))
- Pydantic
- [pyfoil](https://github.com/airgproducts/pyfoil)
- [euklid](https://github.com/airgproducts/euklid)
- **[VTK](https://www.vtk.org/)** - visual toolkit for 3d-output
- Qt - Gui toolkit
