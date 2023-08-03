from typing import Dict, Any, List, Tuple, TypeAlias
from collections.abc import Callable
import re
import json
import io
import logging

#import openglider
import openglider.version
from openglider.jsonify.encoder import Encoder

logger = logging.getLogger(__name__)


MigrationList: TypeAlias = list[tuple[str, Callable]]

class Migration:
    migrations: MigrationList = []

    def __init__(self, jsondata: dict[str, Any]):
        self.json_data = jsondata

        metadata = jsondata.get("MetaData", {})
        version = metadata.get("version", openglider.version.__version__)

        old_version_match = re.match(r"^([0-9]+)\.([0-9]+)$", version)
        if old_version_match:
            major, minor = old_version_match.groups()

            minor = min(6, int(minor))
            version = f"0.0.{minor}"

        self.from_version = version
    
    @staticmethod
    def to_dict(data: Any) -> dict[str, Any]:
        # TODO: improve (speed-wise)!
        return json.loads(json.dumps(data, cls=Encoder))
    
    def migrate(self) -> str:
        jsondata = self.json_data
        #with open("/tmp/data.json", "w") as outfile:
        #    json.dump(jsondata, outfile, indent=2)
        for migration_version, migration in self.get_migrations():
            if self.from_version < migration_version:
                logger.info(f"running migration: {migration_version} / {migration.__name__}")
                jsondata = migration(jsondata)
                logger.info(f"migration {migration.__name__} done")
        
        return json.dumps(jsondata, cls=Encoder)
    
    @classmethod
    def add(cls, to_version: str) -> Callable[[Callable], None]:
        """
        add new migration. version parameter is the version to migrate to
        """
        def decorate(function: Callable) -> None:
            def function_wrapper(jsondata: dict[str, Any]) -> dict[str, Any]:
                logger.info(f"migrating to {to_version}")
                return function(cls, jsondata)

            function_wrapper.__doc__ = function.__doc__
            function_wrapper.__name__ = function.__name__
            cls.migrations.append((to_version, function_wrapper))
        
        return decorate

    @property
    def required(self) -> bool:
        return len(self.get_migrations()) > 0
    
    def get_migrations(self) -> MigrationList:
        migrations: MigrationList = []
        for m in self.migrations:
            if self.from_version < m[0]:
                migrations.append(m)
        
        migrations.sort(key=lambda l: l[0])

        return migrations
    
    @classmethod
    def refactor(cls, jsondata: dict[str, Any], target_module: str, name: str=r".*", module: str=r".*") -> dict[str, Any]:
        for node in cls.find_nodes(jsondata, name, module):
            node["_module"] = target_module
        
        return jsondata
    
    @classmethod
    def find_nodes(cls, jsondata: dict[str, Any], name: str=r".*", module: str=r".*") -> list[dict[str, Any]]:
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
