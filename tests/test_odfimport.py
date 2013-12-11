__author__ = 'simon'
import openglider.Import.ODFImport as ODFImport
import unittest

doc = ODFImport.odfimport("/home/simon/OpenGlider/tests/testkite.ods")
print(ODFImport.sheettolist(doc[0]))
"""
class TestODF(unittest.TestCase):
    def setUp(self):
        self.odf = ODFImport.OdfImport("testglider.ods")

    def test_sheetimport(self):
        print(ODFImport.sheettolist(self.odf[0]))

if __name__ == '__main__':
        unittest.main(verbosity=2)
        """
