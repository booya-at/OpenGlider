


import re
from openglider.glider.glider import Glider
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.glider.rib.rib import Rib
from openglider.utils.table import Table

def fmt(value: float) -> str:
    return str(int(value * 1000))

regex_attachment_point = re.compile(r"([A-Za-z]+)(\d+)")
def get_linesheet_diff(glider: Glider) -> Table:
    table = Table()
    layers = set()
    checklengths: list[dict[str, float]] = []

    for rib in glider.ribs:
        checklengths_temp = {}

        for p in rib.attachment_points:
            if p.rib_pos < 1:
                match = regex_attachment_point.match(p.name)

                if match:
                    layer = match.group(1)
                    layers.add(layer)

                    checklengths_temp[layer] = glider.lineset.get_checklength(p)
        
        if len(checklengths_temp) > 0:
            checklengths.append(checklengths_temp)

    layers_sorted = list(layers)
    layers_sorted.sort()

    table[0, 0] = "Nr."
    for i, layer in enumerate(layers_sorted):
        table[0, i+1] = layer

    
    inner_length: float | None = None

    for row_no, row in enumerate(checklengths):
        first_length = row[layers_sorted[0]]
        table[row_no+1, 0] = str(row_no)

        if inner_length is not None:
            table[row_no+1, 1] = fmt(first_length - inner_length)

        for layer_no, layer in enumerate(layers_sorted[1:]):
            if layer in row:
                table[row_no+1, layer_no+2] = fmt(row[layer] - first_length)
        
        inner_length = first_length
    
    return table




    
