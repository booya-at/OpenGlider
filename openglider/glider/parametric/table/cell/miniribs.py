from openglider.glider.rib import MiniRib

from openglider.glider.parametric.table.elements import CellTable, Keyword

class MiniRibTable(CellTable):
    keywords = {
        "MINIRIB": Keyword(["yvalue", "front_cut"], target_cls=MiniRib)
    }

    def get_element(self, row: int, keyword, data, **kwargs) -> MiniRib:
        elem = super().get_element(row, keyword, data)
        elem.name = f"minirib_{row}_{data[0]:02f}"
        return elem
