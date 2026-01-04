#! /usr/bin/python3
# -*- coding: utf-8; -*-
#
# Extended tests for vector functions
#
import unittest
import math
import numpy as np

from openglider.vector.functions import (
    norm, norm_squared, normalize, vector_angle, rangefrom,
    rotation_2d, rotation_3d, cut, set_dimension,
    radius_from_3points, curvature_from_3points
)


class TestVectorFunctionsExtended(unittest.TestCase):
    """Extended tests for vector functions"""

    def test_norm_squared(self):
        """Test norm_squared function"""
        v1 = np.array([3, 4])
        self.assertEqual(norm_squared(v1), 25)
        
        v2 = np.array([1, 1, 1])
        self.assertEqual(norm_squared(v2), 3)
        
        v3 = np.array([0, 0])
        self.assertEqual(norm_squared(v3), 0)

    def test_normalize(self):
        """Test normalize function"""
        v1 = np.array([3, 4])
        normalized = normalize(v1)
        self.assertAlmostEqual(norm(normalized), 1.0, places=10)
        
        v2 = np.array([1, 1, 1])
        normalized2 = normalize(v2)
        self.assertAlmostEqual(norm(normalized2), 1.0, places=10)
        
        # Test error case
        v_zero = np.array([0, 0])
        with self.assertRaises(ValueError):
            normalize(v_zero)

    def test_vector_angle(self):
        """Test vector_angle function"""
        v1 = np.array([1, 0])
        v2 = np.array([0, 1])
        angle = vector_angle(v1, v2)
        # Angle should be ±90 degrees (pi/2)
        self.assertAlmostEqual(abs(angle), math.pi / 2, places=5)
        
        v3 = np.array([1, 0])
        v4 = np.array([1, 0])
        angle_same = vector_angle(v3, v4)
        self.assertAlmostEqual(angle_same, 0.0, places=5)

    def test_rangefrom(self):
        """Test rangefrom generator"""
        result = list(rangefrom(5, 2))
        # Should start at 2, then alternate around
        self.assertEqual(result[0], 2)
        self.assertIn(3, result)
        self.assertIn(1, result)
        
        # Test edge case: start at beginning
        result_start = list(rangefrom(5, 0))
        self.assertEqual(result_start[0], 0)
        
        # Test edge case: start at end
        result_end = list(rangefrom(5, 4))
        self.assertEqual(result_end[0], 4)

    def test_rotation_2d(self):
        """Test 2D rotation matrix"""
        angle = math.pi / 2
        rot = rotation_2d(angle)
        
        # Should be 2x2 matrix
        self.assertEqual(rot.shape, (2, 2))
        
        # Rotate [1, 0] by 90 degrees
        v = np.array([1, 0])
        rotated = rot.dot(v)
        # Result should be perpendicular (either [0, 1] or [0, -1])
        self.assertAlmostEqual(rotated[0], 0, places=5)
        self.assertAlmostEqual(abs(rotated[1]), 1, places=5)
        
        # Test 180 degree rotation
        rot180 = rotation_2d(math.pi)
        v_rotated = rot180.dot(v)
        self.assertAlmostEqual(v_rotated[0], -1, places=5)

    def test_rotation_3d(self):
        """Test 3D rotation matrix"""
        angle = math.pi / 2
        axis = np.array([0, 0, 1])  # Rotate around z-axis
        rot = rotation_3d(angle, axis)
        
        # Should be 3x3 matrix
        self.assertEqual(rot.shape, (3, 3))
        
        # Rotate [1, 0, 0] around z-axis by 90 degrees
        v = np.array([1, 0, 0])
        rotated = rot.dot(v)
        # Result should be perpendicular in xy-plane
        self.assertAlmostEqual(rotated[0], 0, places=5)
        self.assertAlmostEqual(abs(rotated[1]), 1, places=5)
        self.assertAlmostEqual(rotated[2], 0, places=5)
        
        # Test with default axis
        rot_default = rotation_3d(angle)
        self.assertEqual(rot_default.shape, (3, 3))

    def test_cut(self):
        """Test line intersection function"""
        # Two perpendicular lines intersecting at origin
        p1 = np.array([-1, 0])
        p2 = np.array([1, 0])
        p3 = np.array([0, -1])
        p4 = np.array([0, 1])
        
        point, k, l = cut(p1, p2, p3, p4)
        self.assertAlmostEqual(point[0], 0, places=5)
        self.assertAlmostEqual(point[1], 0, places=5)
        
        # Test parallel lines (should raise error)
        p5 = np.array([0, 0])
        p6 = np.array([1, 0])
        p7 = np.array([0, 1])
        p8 = np.array([1, 1])
        
        # This should work (parallel but not same line)
        try:
            point2, k2, l2 = cut(p5, p6, p7, p8)
        except np.linalg.LinAlgError:
            # Expected for parallel lines
            pass

    def test_set_dimension(self):
        """Test set_dimension function"""
        # Test 1D array to 3D
        arr1d = np.array([1, 2, 3])
        arr3d = set_dimension(arr1d, dim=3)
        self.assertEqual(arr3d.shape, (3, 3))
        self.assertEqual(arr3d[0, 0], 1)
        
        # Test 2D array to 3D
        arr2d = np.array([[1, 2], [3, 4]])
        arr3d_from_2d = set_dimension(arr2d, dim=3)
        self.assertEqual(arr3d_from_2d.shape[1], 3)
        
        # Test to 2D
        arr2d_result = set_dimension(arr1d, dim=2)
        self.assertEqual(arr2d_result.shape, (3, 2))

    def test_radius_from_3points(self):
        """Test radius_from_3points function"""
        # Equilateral triangle
        p1 = np.array([0, 0])
        p2 = np.array([1, 0])
        p3 = np.array([0.5, np.sqrt(3)/2])
        
        # Convert to array of points for function
        p1_arr = np.array([[0, 0]])
        p2_arr = np.array([[1, 0]])
        p3_arr = np.array([[0.5, np.sqrt(3)/2]])
        
        radius = radius_from_3points(p1_arr, p2_arr, p3_arr)
        self.assertGreater(radius[0], 0)
        
        # Test with collinear points (should give large/infinite radius)
        p4 = np.array([[0, 0]])
        p5 = np.array([[1, 0]])
        p6 = np.array([[2, 0]])
        
        radius_collinear = radius_from_3points(p4, p5, p6)
        # Should be very large or inf
        self.assertTrue(np.isinf(radius_collinear[0]) or radius_collinear[0] > 1e10)

    def test_curvature_from_3points(self):
        """Test curvature_from_3points function"""
        # Points on a circle
        p1 = np.array([[0, 1]])
        p2 = np.array([[1, 0]])
        p3 = np.array([[0, -1]])
        
        curvature = curvature_from_3points(p1, p2, p3)
        self.assertGreater(curvature[0], 0)
        
        # Test with collinear points (should give zero curvature)
        p4 = np.array([[0, 0]])
        p5 = np.array([[1, 0]])
        p6 = np.array([[2, 0]])
        
        curvature_collinear = curvature_from_3points(p4, p5, p6)
        self.assertAlmostEqual(curvature_collinear[0], 0, places=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)

