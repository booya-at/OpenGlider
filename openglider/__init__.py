import logging
from pathlib import Path
from typing import Any

from openglider.version import __version__
from openglider.config import config
import openglider.jsonify
import openglider.glider

logger = logging.getLogger(__name__)

def load(filename: str) -> Any:
    """
    """
    if filename.endswith(".ods"):
        res = openglider.glider.GliderProject.import_ods(filename)
    elif filename.lower().endswith(".fcstd") or filename.lower().endswith(".fcstd1"):
        res = openglider.glider.GliderProject.import_freecad(filename)
    else:
        with open(filename) as infile:
            res = openglider.jsonify.load(infile)
        if isinstance(res, dict) and "data" in res:
            logger.info(f"loading file: {filename}")
            logger.info(res["MetaData"])
            
            return res["data"]

    return res

def load_demokite() -> openglider.glider.GliderProject:
    import os
    filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests/common/demokite.ods")

    if not os.path.isfile(filename):
        raise FileNotFoundError()

    return load(filename)

def save(data: Any, filename: str | Path, add_meta: bool=True) -> None:
    with open(filename,"w") as outfile:
        openglider.jsonify.dump(data, outfile, add_meta=add_meta)
