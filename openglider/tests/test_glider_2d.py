import unittest

import tempfile
from openglider.tests.common import GliderTestCase
from openglider import jsonify
from openglider.glider import ParametricGlider

TEMPDIR =  tempfile.gettempdir()

class GliderTestCase2D(GliderTestCase):
    def test_fit(self) -> None:
        self.assertEqualGlider2D(ParametricGlider.fit_glider_3d(self.glider), self.parametric_glider)

    def test_create_glider(self) -> None:
        glider = self.parametric_glider.get_glider_3d()
        self.assertAlmostEqual(glider.span, 2*self.parametric_glider.shape.span, 2)

    def test_export(self) -> None:
        exp = jsonify.dumps(self.parametric_glider)
        imp = jsonify.loads(exp)['data']
        self.assertEqualGlider2D(self.parametric_glider, imp)

        #def test_export_ods(self) -> None:

    def test_set_area(self) -> None:
        self.parametric_glider.shape.set_area(10)
        self.assertAlmostEqual(self.parametric_glider.shape.area, 10)

if __name__ == '__main__':
    unittest.main(verbosity=2)