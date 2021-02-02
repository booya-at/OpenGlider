import getpass
import platform

from openglider.utils import Config


class GlobalConfig(Config):
    asinc_interpolation_points = 2000
    caching = True
    debug = False
    json_allowed_modules = [r"openglider\..*", r"openglider_cpp\..*"]
    json_forbidden_modules = [r".*eval", r".*subprocess.*"]
    user = "{}/{}".format(platform.node(), getpass.getuser())


config = GlobalConfig()


def get(kw):
    return config[kw]

