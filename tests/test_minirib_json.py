import sys
import os
import unittest
import json
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies that might be missing in test env
sys.modules["pyexcel_ods"] = MagicMock()
sys.modules["pyexcel_ods3"] = MagicMock()
sys.modules["ezodf"] = MagicMock()
sys.modules["meshpy"] = MagicMock()
sys.modules["meshpy.triangle"] = MagicMock()
sys.modules["meshpy._internals"] = MagicMock()
sys.modules["svgwrite"] = MagicMock()
sys.modules["svgwrite"] = MagicMock()
sys.modules["svgwrite.container"] = MagicMock()
sys.modules["svgwrite.shapes"] = MagicMock()
sys.modules["svgwrite.path"] = MagicMock()
sys.modules["svgwrite.image"] = MagicMock()

import openglider
from openglider.glider.rib import MiniRib
from openglider import jsonify

class TestMiniRibsSerialization(unittest.TestCase):
    def test_jsonify_minirib(self):
        mr = MiniRib(
            yvalue=0.5, 
            intrados_start=0.8, 
            intrados_end=0.99,
            extrados_start=0.75,
            extrados_end=0.99,
            name="test_mr"
        )
        
        # Test serialization using openglider.jsonify
        try:
            json_str = jsonify.dumps(mr, add_meta=False)
            print(f"Serialized JSON: {json_str}")
        except Exception as e:
            self.fail(f"jsonify.dumps failed: {e}")
            
        # Verify content
        data = json.loads(json_str)
        self.assertEqual(data["_type"], "MiniRib")
        self.assertEqual(data["data"]["yvalue"], 0.5)
        self.assertEqual(data["data"]["intrados_start"], 0.8)
        self.assertEqual(data["data"]["extrados_start"], 0.75)
        self.assertEqual(data["data"]["name"], "test_mr")

if __name__ == "__main__":
    unittest.main()
