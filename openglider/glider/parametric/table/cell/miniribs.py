from openglider.glider.rib import MiniRib

from openglider.glider.parametric.table.elements import ElementTable

class MiniRibTable(ElementTable):
    keywords = [
        ("MINIRIB", 2) # yvalue, front_cut
    ]

    def get_element(self, row: int, keyword, data, **kwargs) -> MiniRib:
        return MiniRib(data[0], data[1], name=f"minirib_{row}_{data[0]:02f}")