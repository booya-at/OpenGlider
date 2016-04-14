import re

colour_patterns = [
    re.compile(r".*(#[0-9A-F]*).*")
]
css_forbidden_chars = ['~', '!', '@', '$', '%', '^', '&', '*', '(', ')', '+', '=', ',', '.', '/', "'", ';', ':', '"', '?',
                   '>', '<', '[', ']', '\\', '{', '}', '|', '`', '#'] #, ' '
default_colour = "FFFFFF"  # white


def normalize_class_names(code):
    new = code
    for char in css_forbidden_chars:
        new = new.replace(char, "")
    return new


def get_material_color(code):
    code_upper = code.upper()
    for pattern in colour_patterns:
        match = pattern.match(code_upper)
        if match:
            return match.groups()[0]

    #return default_colour