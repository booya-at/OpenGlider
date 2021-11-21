from openglider.glider.rib import MiniRib

from openglider.glider.parametric.table.elements import ElementTable, Keyword

class MiniRibTable(ElementTable):
    keywords = {
        "MINIRIB": Keyword(["yvalue", "front_cut"])
    }

    def get_element(self, row: int, keyword, data, **kwargs) -> MiniRib:
        elem = super().get_element(row, keyword, data)
        elem.name = f"minirib_{row}_{data[0]:02f}"
        return elem
