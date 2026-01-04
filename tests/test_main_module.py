#! /usr/bin/python3
# -*- coding: utf-8; -*-
#
# Tests for main openglider module (load/save functions)
#
import unittest
import tempfile
import os
import sys
import json

# Add tests directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openglider
from openglider import jsonify
from common import TestCase


class TestMainModule(TestCase):
    """Tests for main openglider module"""

    def test_load_json(self):
        """Test loading JSON file"""
        # Use the common test data path
        import os
        test_data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "common", "demokite.json"
        )
        glider2d = openglider.load(test_data_path)
        self.assertIsNotNone(glider2d)

    def test_save_load_roundtrip(self):
        """Test save and load roundtrip"""
        glider_2d = self.import_glider_2d()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            openglider.save(glider_2d, tmp_path, add_meta=True)
            
            # Load it back
            loaded = openglider.load(tmp_path)
            
            # Check that it's the same type
            self.assertEqual(type(loaded), type(glider_2d))
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_save_without_meta(self):
        """Test saving without metadata"""
        glider_2d = self.import_glider_2d()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            openglider.save(glider_2d, tmp_path, add_meta=False)
            
            # Check file exists
            self.assertTrue(os.path.exists(tmp_path))
            
            # Load and verify
            loaded = openglider.load(tmp_path)
            self.assertIsNotNone(loaded)
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file"""
        with self.assertRaises((FileNotFoundError, IOError)):
            openglider.load("nonexistent_file.json")

    def test_save_to_invalid_path(self):
        """Test saving to invalid path"""
        glider_2d = self.import_glider_2d()
        
        # Try to save to non-existent directory
        invalid_path = "/nonexistent/directory/file.json"
        with self.assertRaises((FileNotFoundError, IOError, OSError)):
            openglider.save(glider_2d, invalid_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)

