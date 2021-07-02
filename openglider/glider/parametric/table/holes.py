from openglider.glider.parametric.table.elements import ElementTable

from openglider.glider.rib.elements import RibHole, RibSquareHole

class HolesTable(ElementTable):
    keywords = (
        ["HOLE", 2],
        ["QUERLOCH", 2]
    )
    
    def get_element(self, keyword, data):
        if keyword in ("HOLE", "QUERLOCH"):
            return RibHole(data[0], data[1])