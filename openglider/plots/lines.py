import collections

import openglider.lines


def create_line_tree(glider):
    lineset = glider.lineset
    assert isinstance(lineset, openglider.lines.LineSet)
    lowest_lines = []
    for line in lineset.lowest_lines:
        nodes = lineset.get_upper_influence_node(line)
        xval = sum([node.rib_pos for node in nodes])/len(nodes)
        lowest_lines.append((xval, line))

    lowest_lines.sort(key=lambda val: val[0])


    def recursive_get_upper(node):
        dct = collections.OrderedDict()
        for line in lineset.get_upper_connected_lines(node):
            dct[line] = recursive_get_upper(line.upper_node)
        return dct

    return collections.OrderedDict([(line, recursive_get_upper(line.upper_node)) for _, line in lowest_lines])


from openglider.glider.glider_2d import Glider2D


glider = Glider2D.import_ods("/tmp/akkro5.ods")
print(create_line_tree(glider.get_glider_3d()))