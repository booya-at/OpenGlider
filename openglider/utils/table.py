import copy
import re

import ezodf


class Table:
    rex = re.compile(r"([A-Z]*)([0-9]*)")

    @classmethod
    def str_decrypt(cls, str):
        result = cls.rex.match(str.upper())
        if result:
            column, row = result.groups()
            column_no = 0
            for i, character in enumerate(column[::-1]):
                column_no += (26**i)*(ord(character)-64)

            row_no = int(row)

            return column_no-1, row_no-1

        raise ValueError

    @classmethod
    def str_encrypt(cls, column, row):

        return cls.column_to_char(column + 1) + str(row + 1)

    @classmethod
    def column_to_char(cls, x):
        base = 26
        out = ""
        #x -= 1
        while x:
            out += chr(((x-1) % base)+65)
            x = int((x-1)/base)
        return out[::-1]

    def __init__(self, rows=0, columns=0):
        self.dct = {}
        self.num_rows = rows
        self.num_columns = columns

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            row_no, column_no = key
        else:
            column_no, row_no = self.str_decrypt(key)
        self.set(column_no, row_no, value)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            row_no, column_no = item
            item = self.str_encrypt(column_no, row_no)
        return self.dct.get(item, None)

    def __isub__(self, other):
        import numbers
        for key in other.dct:
            zwei = other[key]

            if key in self.dct:
                eins = self[key]
            else:
                if isinstance(zwei, numbers.Number):
                    eins = 0
                else:
                    eins = ""

            if isinstance(eins, numbers.Number) and isinstance(zwei, numbers.Number):
                self[key] = eins - zwei
            else:
                self[key] = str(eins) + " - " + str(zwei)

        return self

    def __sub__(self, other):
        cpy = copy.deepcopy(self)
        cpy -= other

        return cpy

    def set(self, column_no, row_no, value):
        self.num_columns = max(column_no+1, self.num_columns)
        self.num_rows = max(row_no+1, self.num_rows)
        key = self.str_encrypt(column_no, row_no)
        self.dct[key] = value

    def insert_row(self, row, row_no=None):
        if row_no is None:
            row_no = self.num_rows
        for i, el in enumerate(row):
            self.set(i, row_no, el)

    def get(self, column_no, row_no):
        key = self.str_encrypt(column_no, row_no)
        return self.dct.get(key, None)

    def append_right(self, table):
        col = self.num_columns
        for row_no in range(table.num_rows):
            for column_no in range(table.num_columns):
                value = table.get(column_no, row_no)
                if value is not None:
                    self.set(col+column_no, row_no, value)

    def append_bottom(self, table):
        total_rows = self.num_rows
        for row_no in range(table.num_rows):
            for column_no in range(table.num_columns):
                value = table.get(column_no+1, row_no+1)
                if value is not None:
                    self.set(column_no+1, total_rows+row_no+1, value)

    def get_ods_sheet(self, name=None):
        ods_sheet = ezodf.Table(size=(self.num_rows, self.num_columns))
        for key in self.dct:
            column, row = self.str_decrypt(key)
            ods_sheet[row, column].set_value(self.dct[key])

        if name:
            ods_sheet.name = name

        return ods_sheet

    def save(self, path):
        doc = ezodf.newdoc(doctype="ods", filename=path)
        doc.sheets.append(self.get_ods_sheet())
        doc.save()
        return doc

    @classmethod
    def load(cls, path):
        doc = ezodf.opendoc(path)
        sheets = [cls.from_ods_sheet(sheet) for sheet in doc.sheets]
        if len(sheets) == 1:
            return sheets[0]
        return sheets

    @classmethod
    def from_ods_sheet(cls, sheet):
        num_rows = sheet.nrows()
        num_cols = sheet.ncols()
        table = cls()

        for row in range(num_rows):
            for col in range(num_cols):
                value = sheet.get_cell([row, col]).value
                if value is not None:
                    table[row, col] = value

        return table


    def _repr_html_(self):
        html = "<table><thead><td></td>"
        for column_no in range(self.num_columns):
            html += "<td>{}</td>".format(self.column_to_char(column_no + 1))

        html += "</thead>"
        for row_no in range(self.num_rows):
            html += "<tr><td>{}</td>".format(row_no+1)
            for column_no in range(self.num_columns):
                ident = self.str_encrypt(column_no, row_no)
                value = self.dct.get(ident, "")
                if isinstance(value, float):
                    value = round(value, 3)
                html += "<td>{}</td>".format(value)
            html += "</tr>"

        html += "</table>"

        return html

