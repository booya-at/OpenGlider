import collections

import ezodf

import openglider.lines


def create_line_tree(glider):
    """
    Create a tree of lines (ordered dict)
    """
    lineset = glider.lineset
    assert isinstance(lineset, openglider.lines.LineSet)
    lowest_lines = []
    for line in lineset.lowest_lines:
        nodes = lineset.get_upper_influence_nodes(line)
        xval = sum([node.rib_pos for node in nodes])/len(nodes)
        lowest_lines.append((xval, line))

    lowest_lines.sort(key=lambda val: val[0])

    def recursive_get_upper(node):
        dct = collections.OrderedDict()
        upper_lines = lineset.get_upper_connected_lines(node)

        def sort_key(line):
            nodes = lineset.get_upper_influence_nodes(line)
            values = [glider.ribs.index(node.rib)*100+node.rib_pos for node in nodes]
            return sum(values)/len(values)

        upper_lines.sort(key=sort_key)
        # sort by: 100*rib_no + x_value
        for line in upper_lines:
            dct[line] = recursive_get_upper(line.upper_node)
        return dct

    return collections.OrderedDict([(line, recursive_get_upper(line.upper_node)) for _, line in lowest_lines])


def output_lines(glider, ods_sheet=None):

    line_tree = glider.lineset.create_tree()
    ods_sheet = ods_sheet or ezodf.Table(name="lines", size=(500, 500))

    floors = max(glider.lineset.floors)

    def insert_block(line, upper, row, column):
        length = round(line.get_stretched_length()*1000)
        ods_sheet[row, column].set_value(length)
        ods_sheet[row, column + floors+3].set_value(line.type.name)
        if upper:
            for line, line_upper in upper:
                row = insert_block(line, line_upper, row, column-1)
        else:  # Insert a top node
            name = line.upper_node.name
            if not name:
                name = "Rib_{}/{}".format(glider.ribs.index(line.upper_node.rib),
                                          line.upper_node.rib_pos)
            ods_sheet[row, column-1].set_value(name)
            ods_sheet[row, column+2+floors].set_value(name)
            row += 1
        return row

    row = 1
    for line, upper in line_tree:
        row = insert_block(line, upper, row, floors)

    return ods_sheet


if __name__ == "__main__":
    from openglider.glider import ParametricGlider

    glider = ParametricGlider.import_ods("/tmp/akkro5.ods")
    #tree=create_line_tree(glider.get_glider_3d())
    sheet = output_lines(glider.get_glider_3d())

    ods=ezodf.newdoc("ods", "/tmp/lines.ods")
    ods.sheets += sheet
    ods.save()
