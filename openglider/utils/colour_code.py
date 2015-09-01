import re

colour_patterns = [
    re.compile(r".*#([0-9A-F]*).*")
]
default_colour = "FFFFFF"  # white


def get_material_color(code):
    for pattern in colour_patterns:
        match = pattern.match(code)
        if match:
            return match.groups()[0]

    return default_colour