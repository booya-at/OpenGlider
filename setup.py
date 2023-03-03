import pathlib
import re

from distutils.core import setup

packages, package_data = [], {}

root_dir = pathlib.Path(__file__).absolute().parent / "openglider"

packages = ["openglider"]
for path in root_dir.iterdir():
    dirname = path.stem + path.suffix
    if dirname in ("__pycache__", "tests"):
        continue

    if path.is_dir():
        packages.append(f"openglider.{dirname}")


package_data["openglider"] = ["py.typed"]

with open("openglider/version.py") as version_file:
    #print(version_file.read())
    version_str = version_file.read()
    match = re.match(r"__version__\s=\s['\"]([0-9\._]+)['\"]", version_str)
    
    if match is not None:
        version = match.group(1)
    else:
        raise ValueError(f"No match for version string: {version_str}")

with open("README.md") as readme_file:
    long_description = readme_file.read()

setup(
    name='OpenGlider',
    version=version,
    description="tool for glider design",
    packages=packages,
    package_data=package_data,
    license='GPL-v3',
    long_description=long_description,
    install_requires=[
        "euklid",
        "pyfoil",
        "pydantic",
        "svgwrite",
        "numpy",
        "scipy",
        "ezdxf",
        "ezodf",
        "lxml", # missing in ezodf:q;
        "pyexcel-ods",
        "meshpy",
        "svglib"
    ],
    extras_require={
        "gui": [
            "qtpy",
            "pyside2",
            "qtawesome",
            "qasync",
            "qtmodern",
            "qtconsole",
            "iconify",
            "pyqtgraph",
            "matplotlib",
            "vtk"
        ]
    },
    author='airG products',
    url='https://airg.family/',
    include_package_data=True
)
