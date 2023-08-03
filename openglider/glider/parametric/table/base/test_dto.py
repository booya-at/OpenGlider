import unittest
from openglider.glider.parametric.table.base.dto import DTO, CellTuple
from openglider.vector.unit import Length, Percentage

class DtoWithAllTypes(DTO):
    a: str
    b: float
    d: Percentage | Length
    c: Percentage
    e: CellTuple[Percentage | Length]
    

class TestDTO(unittest.TestCase):

    def test_descriptor(self) -> None:
        result = DtoWithAllTypes.describe()

        self.assertEqual(result[0], ("a", "str"))
        self.assertEqual(result[1], ("b", "float"))
        self.assertEqual(result[2], ("d", "Percentage | Length"))
        self.assertEqual(result[3], ("c", "Percentage"))
        self.assertEqual(result[4], ("e (1)", "Percentage | Length"))
        self.assertEqual(result[5], ("e (2)", "Percentage | Length"))

    def test_units(self) -> None:
        obj = DtoWithAllTypes(
            a = "str",
            b = 1.2,
            c = 0.5,  # type: ignore
            d = "100%",  # type: ignore
            e = ("0.5m", "50cm")  # type: ignore
        )

        self.assertEqual(obj.b, 1.2)
        self.assertEqual(obj.c.si, 0.5)
        self.assertEqual(obj.d.si, 1.)
        self.assertEqual(obj.e.first, obj.e.second)

if __name__ == "__main__":
    unittest.main()