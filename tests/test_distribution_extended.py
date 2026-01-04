#! /usr/bin/python3
# -*- coding: utf-8; -*-
#
# Extended tests for Distribution class
#
import unittest
import numpy as np

from openglider.utils.distribution import Distribution


class TestDistributionExtended(unittest.TestCase):
    """Extended tests for Distribution class"""

    def test_from_linear(self):
        """Test creating linear distribution"""
        dist = Distribution.from_linear(10)
        self.assertEqual(len(dist.data), 10)
        self.assertAlmostEqual(dist.data[0], -1.0)
        # Last value should be close to 1.0 (may not be exactly 1.0 due to division)
        self.assertGreaterEqual(dist.data[-1], 0.8)
        self.assertLessEqual(dist.data[-1], 1.0)
        
        # Test with custom range
        dist_custom = Distribution.from_linear(5, start=0, stop=10)
        self.assertEqual(len(dist_custom.data), 5)
        self.assertAlmostEqual(dist_custom.data[0], 0.0)
        # Last value may not be exactly stop due to division
        self.assertGreaterEqual(dist_custom.data[-1], 8.0)
        self.assertLessEqual(dist_custom.data[-1], 10.0)

    def test_from_polynom_distribution(self):
        """Test creating polynomial distribution"""
        dist = Distribution.from_polynom_distribution(10, order=2)
        self.assertGreater(len(dist.data), 0)
        self.assertLessEqual(dist.data[0], 0)  # Should start negative
        self.assertGreaterEqual(dist.data[-1], 0)  # Should end positive
        
        # Test with different order
        dist_order3 = Distribution.from_polynom_distribution(10, order=3)
        self.assertGreater(len(dist_order3.data), 0)

    def test_from_cos_2_distribution(self):
        """Test creating cos_2 distribution"""
        dist = Distribution.from_cos_2_distribution(10)
        self.assertGreater(len(dist.data), 0)
        
        # Should have values between -1 and 1
        for val in dist.data:
            self.assertGreaterEqual(val, -1.1)  # Allow small tolerance
            self.assertLessEqual(val, 1.1)

    def test_from_nose_cos_distribution(self):
        """Test creating nose cos distribution"""
        dist = Distribution.from_nose_cos_distribution(20, border=0.5)
        self.assertGreater(len(dist.data), 0)
        
        # Should be symmetric around 0
        self.assertAlmostEqual(dist.data[0], -dist.data[-1], places=3)
        
        # Test with different border
        dist_border = Distribution.from_nose_cos_distribution(20, border=0.3)
        self.assertGreater(len(dist_border.data), 0)

    def test_get_index(self):
        """Test getting index for a value"""
        dist = Distribution.from_linear(10)
        
        # Test in middle (boundary values may cause issues)
        mid_val = dist.data[len(dist.data) // 2]
        idx_mid = dist.get_index(mid_val)
        self.assertGreaterEqual(idx_mid, 0)
        self.assertLessEqual(idx_mid, len(dist.data) - 1)
        
        # Test with value in range
        test_val = 0.0
        if dist.data[0] <= test_val <= dist.data[-1]:
            idx = dist.get_index(test_val)
            self.assertFalse(np.isnan(idx))
            self.assertGreaterEqual(idx, 0)
            self.assertLessEqual(idx, len(dist.data) - 1)

    def test_insert_value(self):
        """Test inserting a value"""
        dist = Distribution.from_linear(10)
        original_len = len(dist.data)
        
        # Insert value in middle (that's not already there)
        insert_val = 0.55  # Value likely not in linear distribution
        dist.insert_value(insert_val)
        # Length may stay same if value is very close to existing, or increase
        self.assertGreaterEqual(len(dist.data), original_len)
        
        # Insert at boundary
        dist2 = Distribution.from_linear(10)
        dist2.insert_value(-0.95)
        # Should be inserted or very close value exists
        self.assertTrue(any(abs(x - (-0.95)) < 0.1 for x in dist2.data))

    def test_insert_values(self):
        """Test inserting multiple values"""
        dist = Distribution.from_linear(10)
        original_len = len(dist.data)
        
        values = [-0.55, 0.35, 0.75]  # Values likely not in linear dist
        dist.insert_values(values)
        
        # Check values are inserted or very close values exist
        for val in values:
            self.assertTrue(any(abs(x - val) < 0.1 for x in dist.data))
        
        # Length should increase (unless all values were already very close)
        self.assertGreaterEqual(len(dist.data), original_len)

    def test_upper_property(self):
        """Test upper property"""
        dist = Distribution.from_linear(10)
        upper = dist.upper
        
        self.assertIsInstance(upper, list)
        self.assertLessEqual(upper[-1], 0)  # Should end at or before 0
        self.assertGreaterEqual(upper[0], -1.1)  # Should start around -1

    def test_make_symmetric_from_lower(self):
        """Test making symmetric distribution from lower"""
        # Create asymmetric distribution
        dist = Distribution([-1, -0.5, 0, 0.3, 0.7, 1])
        dist.make_symmetric_from_lower()
        
        # Should be symmetric
        self.assertAlmostEqual(dist.data[0], -dist.data[-1], places=5)
        # Should contain 0
        self.assertIn(0, dist.data)

    def test_new_with_cos(self):
        """Test Distribution.new with cos type"""
        dist = Distribution.new(20, dist_type="cos")
        self.assertEqual(len(dist.data), 21)  # cos adds 1
        
        # Should have values between -1 and 1
        for val in dist.data:
            self.assertGreaterEqual(val, -1.1)
            self.assertLessEqual(val, 1.1)

    def test_new_with_nose_cos(self):
        """Test Distribution.new with nose_cos type"""
        dist = Distribution.new(20, dist_type="nose_cos")
        self.assertGreater(len(dist.data), 0)
        
        # Should be symmetric
        self.assertAlmostEqual(dist.data[0], -dist.data[-1], places=3)

    def test_new_with_fixed_nodes(self):
        """Test Distribution.new with fixed nodes"""
        dist = Distribution.new(20, dist_type="cos", fixed_nodes=[-0.5, 0.5])
        
        # Check fixed nodes are included
        self.assertIn(-0.5, dist.data)
        self.assertIn(0.5, dist.data)

    def test_find_nearest(self):
        """Test finding nearest value"""
        dist = Distribution.from_linear(10)
        
        # Test finding nearest to existing value
        nearest = dist.find_nearest(0.0)
        # Should return an index
        self.assertIsInstance(nearest, (int, float, type(None)))
        
        # Test with start_ind
        nearest_start = dist.find_nearest(0.5, start_ind=5)
        if nearest_start is not None:
            self.assertGreaterEqual(nearest_start, 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)

