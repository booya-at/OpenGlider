from __future__ import annotations

import csv
import logging

from openglider.lines.line_types.linetype import LineType

logger = logging.getLogger(__name__)


class KnotCorrections:
    knots_table_line_type = tuple[str, str, int, float, float]

    knots_table: list[knots_table_line_type] = [
        # lower_line_type, upper_line_type, upper_line_count, first_line_correction, last_line_correction
        ("liros.ltc65", "liros.ltc65", 2, 2.0, 2.0)
    ]
    knots_dict: dict[str, tuple[float, float]]

    def __init__(self, knots: list[knots_table_line_type] | None=None):
        if knots:
            self.knots_table = knots
        self.knots_dict = {}
        
        self.update()
    
    def save_csv(self, filename: str) -> None:
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["lower_type", "upper_type", "upper_num", "first_line_correction", "last_line_correction"])
            for knot in self.knots_table:
                writer.writerow(knot)
    
    @classmethod
    def read_csv(cls, filename: str) -> KnotCorrections:
        with open(filename) as f:
            reader = csv.reader(f)
            lines: list[tuple[str, str, int, float, float]] = []
            
            for i, line in enumerate(reader):
                if i > 0:
                    lines.append((
                        line[0],
                        line[1],
                        int(line[2]),
                        float(line[3]),
                        float(line[4])
                    ))

            return cls(lines)


    @staticmethod
    def _knot_key(line_type_1: LineType | str, line_type_2: LineType | str, upper_num: int) -> str:
        if isinstance(line_type_1, LineType):
            line_type_1 = line_type_1.name
        if isinstance(line_type_2, LineType):
            line_type_2 = line_type_2.name
        return f"{line_type_1}/{line_type_2}/{upper_num}"

    def update(self) -> None:
        self.knots_dict.clear()
        self.knots_table.sort(key=lambda x: self._knot_key(*x[:3]))
        for knot in self.knots_table:
            key = self._knot_key(*knot[:3])
            self.knots_dict[key] = knot[3:]

    def predict(self, lower_type: LineType, upper_type: LineType, num: int) -> tuple[float, float]:
        d1_base = 6.86042156e-01
        d1_num = 2.89561675e-01
        d2_base = 2.67032978
        d2_num = 4.82535042e-02
        sheet_factor = 1.48554646
        count_factor = 7.22786326e-04
        
        d1 = lower_type.thickness
        d2 = upper_type.thickness
    
        d1_sheet = d2_sheet = 1.
        if lower_type.sheated:
            d1_sheet *= sheet_factor
        
        if upper_type.sheated:
            d2_sheet *= sheet_factor
            
            
        base_amount = (d1_base + num * d1_num) * d1 * d1_sheet + (d2_base + num * d2_num) * d2 * d2_sheet
        return (
            base_amount,
            base_amount + count_factor * (num-1)
        )
    
    
    def get(self, lower_type: LineType, upper_type: LineType, upper_num: int) -> list[float]:
        key = self._knot_key(lower_type, upper_type, upper_num)

        if key not in self.knots_dict:
            logger.warning(f"no shortening values for {lower_type} and {upper_type} with {upper_num} top lines")
            first, last = self.predict(lower_type, upper_type, upper_num)
        else:
            try:
                first = self.knots_dict[key][0]
                last = self.knots_dict[key][1]
            except:
                raise Exception(f"whooot {lower_type} and {upper_type} with {upper_num} top")

        return [(first + index * (last-first) / (upper_num-1)) * 0.001 for index in range(upper_num)]

