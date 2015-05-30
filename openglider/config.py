import getpass
import platform

config = {
    "asinc_interpolation_points": 1000,
    "caching": True,
    "debug": False,
    "json_allowed_modules": [r"openglider\..*"],
    "json_forbidden_modules": [r".*eval", r".*subprocess.*"],
    "user": "{}/{}".format(platform.node(), getpass.getuser())

}
