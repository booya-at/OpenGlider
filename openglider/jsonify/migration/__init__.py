import re
import logging

from openglider.jsonify.migration.migration import Migration
import openglider.jsonify.migration.migrate_0_0_8_tables

logger = logging.getLogger(__name__)




@Migration.add("0.0.5")
def migrate_00(cls, jsondata):
    """
    Alter data and return
    :param jsondata:
    :return:
    """
    for node in cls.find_nodes(jsondata, name=r"DrawingArea"):
        node["__class__"] = "Layout"

    return jsondata

@Migration.add("0.0.7")
def migrate_splines_07(cls, jsondata):
    "Migrate spline curves"
    logger.info("migrating to 0.0.7")
    for curvetype in ("Bezier", "SymmetricBezier", "BSpline", "SymmetricBSpline"):
        for node in cls.find_nodes(jsondata, name="^"+curvetype+"$"):
            logger.warning(f'curve:  {node["data"]}')
            node["data"].pop("basefactory", None)
            node["data"].pop("degree", None)
            node["_type"] = f"{curvetype}Curve"
            node["_module"] = "euklid.spline"
    
    return jsondata

@Migration.add("0.0.8")
def migrate_08(cls, jsondata):
    logger.info("migrating to 0.0.8")
    for node in cls.find_nodes(jsondata, module=r"openglider_cpp.*"):
        path_orig = re.match(r"openglider_cpp\.(.*)", node["_module"]).group(1)

        if path_orig == "euklid":
            path = "vector"
        else:
            path = path_orig
            
        node["_module"] = f"euklid.{path}"
    
    for node in cls.find_nodes(jsondata, module=r"openglider.airfoil.parametric"):
        node["_module"] = "openglider.airfoil.profile_2d_parametric"

    return jsondata

