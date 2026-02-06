# -*- coding: utf-8 -*-
"""
Unit tests for openglider.vector.plane.Plane.
"""
import unittest
import numpy as np

from openglider.vector.plane import Plane


class TestPlane(unittest.TestCase):
    """Tests for Plane (point, projection, normvector)."""

    def test_point(self):
        """point(x1, x2) = p0 + x1*v1 + x2*v2."""
        p0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        plane = Plane(p0, v1, v2)
        pt = plane.point(2.0, 3.0)
        np.testing.assert_array_almost_equal(pt, [2.0, 3.0, 0.0])

    def test_normvector_xy_plane(self):
        """Normvector of xy-plane is (0,0,1) or (0,0,-1)."""
        p0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        plane = Plane(p0, v1, v2)
        n = plane.normvector
        self.assertAlmostEqual(np.linalg.norm(n), 1.0)
        self.assertAlmostEqual(abs(n[2]), 1.0)

    def test_projection(self):
        """projection gives coordinates along v1, v2."""
        p0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        plane = Plane(p0, v1, v2)
        pt = np.array([3.0, 4.0, 0.0])
        proj = plane.projection(pt)
        self.assertAlmostEqual(proj[0], 3.0)
        self.assertAlmostEqual(proj[1], 4.0)

    def test_projection_offset_origin(self):
        """projection with p0 != 0."""
        p0 = np.array([1.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        plane = Plane(p0, v1, v2)
        pt = plane.point(2.0, 1.0)  # [3, 1, 0]
        proj = plane.projection(pt)
        self.assertAlmostEqual(proj[0], 2.0)
        self.assertAlmostEqual(proj[1], 1.0)
