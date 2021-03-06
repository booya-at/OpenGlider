import re
import json
import io
import logging

import openglider
import openglider.version

logger = logging.getLogger(__name__)


class Migration:
    migrations = []

    def __init__(self, jsondata):
        self.json_data = jsondata

        metadata = jsondata.get("MetaData", {})
        version = metadata.get("version", openglider.version.__version__)

        old_version_match = re.match(r"([0-9])\.([0-9])([0-9]+)", version)
        if old_version_match:
            version = ".".join(old_version_match.groups())

        self.from_version = version
    
    def migrate(self):
        jsondata = self.json_data
        for migration_version, migration in self.get_migrations():
            if self.from_version < migration_version:
                logger.debug(f"running migration: {migration.__doc__}")
                jsondata = migration(jsondata)
        
        return json.dumps(jsondata)
    
    @classmethod
    def add(cls, version):
        def decorate(function):
            def function_wrapper(jsondata):
                logger.info(f"migrating to {version}")
                return function(cls, jsondata)

            function_wrapper.__doc__ = function.__doc__
            cls.migrations.append([version, function_wrapper])
        
        return decorate

    @property
    def required(self):
        return len(self.get_migrations()) > 0
    
    def get_migrations(self):
        migrations = []
        for m in self.migrations:
            if self.from_version < m[0]:
                migrations.append(m)
        
        migrations.sort(key=lambda l: l[0])

        return migrations
    
    @classmethod
    def find_nodes(cls, jsondata, name=r".*", module=r".*"):
        """
        Find nodes recursive
        :param name: *to find any
        :param module: *to search all
        :param jsondata:
        :return: list of nodes
        """
        rex_name = re.compile(name)
        rex_module = re.compile(module)
        nodes = []
        if isinstance(jsondata, dict):
            if "_type" in jsondata:
                # node
                if rex_name.match(jsondata["_type"]) and rex_module.match(jsondata["_module"]):
                    nodes.append(jsondata)
                else:
                    for value in jsondata["data"].values():
                        nodes += cls.find_nodes(value, name, module)

            else:
                for el in jsondata.values():
                    nodes += cls.find_nodes(el, name, module)
        elif isinstance(jsondata, list):
            for el in jsondata:
                nodes += cls.find_nodes(el, name, module)
        elif isinstance(jsondata, str):
            pass
        else:
            try:
                for el in jsondata:
                    nodes += cls.find_nodes(el, name, module)
            except TypeError:
                pass

        return nodes


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
def migrate_07(cls, jsondata):
    "Migrate spline curves"
    logger.info("migrating to 0.0.7")
    for curvetype in ("Bezier", "SymmetricBezier", "BSpline", "SymmetricBSpline"):
        for node in cls.find_nodes(jsondata, name="^"+curvetype+"$"):
            node["data"].pop("basefactory")
            node["_type"] = f"{curvetype}Curve"
            node["_module"] = "euklid.spline"
    
    
    with open("/tmp/test_07.json", "w") as outfile:
        json.dump(jsondata, outfile, indent=4)
    
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

