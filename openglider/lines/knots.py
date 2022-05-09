from typing import List, Dict, Tuple, Optional, Union
import csv
import logging

from openglider.lines.line_types.linetype import LineType

logger = logging.getLogger(__name__)


class KnotCorrections:
    knots_table_line_type = Tuple[str, str, int, float, float]

    knots_table: List[knots_table_line_type] = [
        # lower_line_type, upper_line_type, upper_line_count, first_line_correction, last_line_correction
        ("liros.ltc65", "liros.ltc65", 2, 2.0, 2.0)
    ]
    knots_dict: Dict[str, Tuple[float, float]]

    def __init__(self, knots: Optional[List[knots_table_line_type]]=None):
        if knots:
            self.knots_table = knots
        self.knots_dict = {}
        
        self.update()
    
    def save_csv(self, filename):
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["lower_type", "upper_type", "upper_num", "first_line_correction", "last_line_correction"])
            for knot in self.knots_table:
                writer.writerow(knot)
    
    @classmethod
    def read_csv(cls, filename):
        with open(filename) as f:
            reader = csv.reader(f)
            lines = []
            
            for i, line in enumerate(reader):
                if i > 0:
                    lines.append([
                        line[0],
                        line[1],
                        int(line[2]),
                        float(line[3]),
                        float(line[4])
                    ])

            return cls(lines)


    @staticmethod
    def _knot_key(line_type_1: Union[LineType, str], line_type_2: Union[LineType, str], upper_num: int):
        if isinstance(line_type_1, LineType):
            line_type_1 = line_type_1.name
        if isinstance(line_type_2, LineType):
            line_type_2 = line_type_2.name
        return f"{line_type_1}/{line_type_2}/{upper_num}"

    def update(self):
        self.knots_dict.clear()
        self.knots_table.sort(key=lambda x: self._knot_key(*x[:3]))
        for knot in self.knots_table:
            key = self._knot_key(*knot[:3])
            self.knots_dict[key] = knot[3:]
    
    def get(self, lower_type, upper_type, upper_num):
        key = self._knot_key(lower_type, upper_type, upper_num)

        if key not in self.knots_dict:
            logger.warning(f"no shortening values for {lower_type} and {upper_type} with {upper_num} top lines")
            return [0] * upper_num

        try:
            first = self.knots_dict[key][0] * 0.001
            last = self.knots_dict[key][1] * 0.001
        except:
            raise Exception(f"whooot {lower_type} and {upper_type} with {upper_num} top")
        
        if upper_num == 1:
            return [first]

        return [first + index * (last-first) / (upper_num-1) for index in range(upper_num)]

