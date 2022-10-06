import re

colour_patterns = [
    re.compile(r".*(#[0-9A-F]*).*")
]
css_forbidden_chars = ['~', '!', '@', '$', '%', '^', '&', '*', '(', ')', '+', '=', ',', '.', '/', "'", ';', ':', '"', '?',
                   '>', '<', '[', ']', '\\', '{', '}', '|', '`', '#'] #, ' '
default_colour = "FFFFFF"  # white
starts_witch_number = re.compile("[0-9].*")

def normalize_class_names(code: str) -> str:
    new = code
    for char in css_forbidden_chars:
        new = new.replace(char, "")

    if starts_witch_number.match(new):
        new = "class_" + new

    return new


def get_material_color(code: str) -> str | None:
    code_upper = code.upper()
    for pattern in colour_patterns:
        match = pattern.match(code_upper)
        if match:
            return match.groups()[0]
    
    return None