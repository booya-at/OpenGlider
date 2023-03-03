import tempfile
import json

from openglider.tests.common import *
from openglider.plots import PlotMaker
from openglider import jsonify


class TestGlider(GliderTestCase):
    def tempfile(self, name: str) -> str:
        return os.path.join(tempfile.gettempdir(), name)

    def test_import_export_ods(self) -> None:
        path = self.tempfile('kite.ods')
        self.parametric_glider.export_ods(path)

    def test_export_obj(self) -> None:
        path = self.tempfile('kite.obj')
        self.glider.get_mesh(midribs=5).export_obj(path)

    def test_export_dxf(self) -> None:
        path = self.tempfile('kite.dxf')
        self.glider.get_mesh(midribs=5).export_dxf(path)

    def test_export_plots(self) -> None:
        path = self.tempfile('kite_plots.svg')
        dxfile = self.tempfile("kite_plots.dxf")
        ntvfile = self.tempfile("kite_plots.ntv")

        patterns = PlotMaker(self.glider)
        patterns.unwrap()

        print(type(patterns), patterns)
        all = patterns.get_all_grouped()

        print(all)


        all.export_svg(path)
        all.export_dxf(dxfile)
        all.export_ntv(ntvfile)

    def test_export_glider_json(self) -> None:
        with open(self.tempfile('kite_3d.json'), "w+") as tmp:
            jsonify.dump(self.glider, tmp)
            tmp.seek(0)
            glider = jsonify.load(tmp)['data']
            
        self.assertEqualGlider(self.glider, glider)

    def test_export_glider_ods(self) -> None:
        path = self.tempfile("kite.ods")
        self.parametric_glider.export_ods(path)
        glider_2d_2 = self.parametric_glider.import_ods(path)
        self.assertEqualGlider2D(self.parametric_glider, glider_2d_2)

    def test_export_glider_json2(self) -> None:
        with open(self.tempfile("kite_2d.json"), "w+") as outfile:
            jsonify.dump(self.parametric_glider, outfile)
            outfile.seek(0)
            glider = jsonify.load(outfile)['data']
        self.assertEqualGlider2D(self.parametric_glider, glider)




if __name__ == '__main__':
    unittest.main(verbosity=2)