from openglider.glider.glider import Glider


def rename_parts(glider: Glider):
    set_strap_names(glider)

    return glider


def set_strap_names(glider: Glider):
    curves = glider.get_attachment_point_layers()

    for cell_no, cell in enumerate(glider.cells):
        cell_layers = []
        for curve_name, curve in curves.items():
            if curve.nodes[-1][0] > cell_no:
                cell_layers.append((curve_name, curve.get_value(cell_no)))


        cell_layers.sort(key=lambda el: el[1])
        
        result = []
        layers_between = {}
        
        def get_name(position: float):
            name = "-"
            
            for layer_name, pct in cell_layers:
                if pct == position:
                    return layer_name
                    
                print(pct, position, name)
                if pct < position:
                    name = layer_name
                
            layers_between.setdefault(name, 0)
            layers_between[name] += 1

            return f"{name}{layers_between[name]}"
            
        straps = cell.straps[:]
        straps.sort(key=lambda strap: strap.get_average_x())
        for strap in cell.straps:
            strap.name = get_name(strap.center_left)
            
        
        return result