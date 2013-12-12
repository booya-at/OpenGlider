__author__ = 'simon'
import openglider.Import.ODFImport2 as ODFImport
import unittest

doc = ODFImport.import_ods("/home/simon/OpenGlider/tests/demokite.ods")



"""
class TestODF(unittest.TestCase):
    def setUp(self):
        self.odf = ODFImport.OdfImport("testglider.ods")

    def test_sheetimport(self):
        print(ODFImport.sheettolist(self.odf[0]))

if __name__ == '__main__':
        unittest.main(verbosity=2)
        """
