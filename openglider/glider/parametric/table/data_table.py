from typing import Dict, List

from openglider.utils.table import Table



class DataTable:
    subdicts: Dict[str, List[type]] = {
        "trim_correction": [str, float]
    }


    def __init__(self, table: Table):
        self.table = table

    def get_dct(self):
        dct = {}
        for row in range(1, self.table.num_rows):
            key = self.table[row, 0]

            if key:
                if key.lower() not in self.subdicts:
                    dct[key] = self.table[row, 1]
                else:
                    key = key.lower()
                    types = self.subdicts[key]
                    row = [self.table[row, i+1] for i in range(len(types))]
                    dct.setdefault(key, [])

                    dct[key].append(tuple(
                        t(x) for t, x in zip(types, row)
                    ))
        
        return dct
