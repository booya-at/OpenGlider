import typing

import re
import json
import io
import logging

#import openglider
import openglider.version
from openglider.jsonify.encoder import Encoder

logger = logging.getLogger(__name__)


class Migration:
    migrations: typing.List[typing.Tuple[str, typing.Callable]] = []

    def __init__(self, jsondata):
        self.json_data = jsondata

        metadata = jsondata.get("MetaData", {})
        version = metadata.get("version", openglider.version.__version__)

        old_version_match = re.match(r"^([0-9]+)\.([0-9]+)$", version)
        if old_version_match:
            major, minor = old_version_match.groups()

            minor = min(6, int(minor))
            version = f"0.0.{minor}"

        self.from_version = version
    
    def migrate(self):
        jsondata = self.json_data
        #with open("/tmp/data.json", "w") as outfile:
        #    json.dump(jsondata, outfile, indent=2)
        for migration_version, migration in self.get_migrations():
            if self.from_version < migration_version:
                logger.warning(f"running migration: {migration_version} / {migration.__name__}")
                jsondata = migration(jsondata)
                logger.warning(f"migration {migration.__name__} done")
        
        return json.dumps(jsondata, cls=Encoder)
    
    @classmethod
    def add(cls, version):
        """
        add new migration. version parameter is the version to migrate to
        """
        def decorate(function):
            def function_wrapper(jsondata):
                logger.info(f"migrating to {version}")
                return function(cls, jsondata)

            function_wrapper.__doc__ = function.__doc__
            function_wrapper.__name__ = function.__name__
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
        if jsondata is None:
            return []
        #logger.warning(f"find nodes: {name}, {jsondata}")
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

        #logger.warning(f"found nodes ({name}): {len(nodes)}")

        return nodes
