import getpass
import platform
from typing import Any

from openglider.utils.config import Config


class GlobalConfig(Config):
    asinc_interpolation_points = 2000
    caching = True
    debug = False
    json_allowed_modules = [r"openglider\..*", r"euklid\..*", r"pyfoil\..*"]
    json_forbidden_modules = [r".*eval", r".*subprocess.*"]
    user = f"{platform.node()}/{getpass.getuser()}"


config = GlobalConfig()


def get(kw: str) -> Any:
    return config[kw]

