# -*- coding: utf-8 -*-
"""
Unit tests for openglider.vector.polygon (Polygon2D, CirclePart, Ellipse, Circle).
"""
import unittest
import numpy as np

from openglider.vector.polygon import Polygon2D, Circle, Ellipse


class TestPolygon2D(unittest.TestCase):
    """Tests for Polygon2D (closed polyline, area, center, contains)."""

    def test_isclosed_true(self):
        """Closed polygon: first point equals last."""
        pts = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
        poly = Polygon2D(pts)
        self.assertTrue(poly.isclosed)

    def test_isclosed_false(self):
        """Open polygon: first != last."""
        pts = [[0, 0], [1, 0], [1, 1], [0, 1]]
        poly = Polygon2D(pts)
        self.assertFalse(poly.isclosed)

    def test_centerpoint(self):
        """Centerpoint is mean of vertices."""
        pts = [[0, 0], [2, 0], [2, 2], [0, 2]]
        poly = Polygon2D(pts)
        c = poly.centerpoint
        self.assertAlmostEqual(c[0], 1.0)
        self.assertAlmostEqual(c[1], 1.0)

    def test_area_rectangle(self):
        """Area of axis-aligned rectangle."""
        pts = [[0, 0], [3, 0], [3, 2], [0, 2], [0, 0]]
        poly = Polygon2D(pts)
        self.assertAlmostEqual(poly.area, 6.0)

    def test_area_triangle(self):
        """Area of triangle (closed)."""
        pts = [[0, 0], [2, 0], [1, 2], [0, 0]]
        poly = Polygon2D(pts)
        self.assertAlmostEqual(abs(poly.area), 2.0)

    def test_contains_point_inside_rect(self):
        """Point inside rectangle."""
        pts = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        poly = Polygon2D(pts)
        self.assertTrue(poly.contains_point(np.array([1, 1])))

    def test_contains_point_outside_rect(self):
        """Point outside rectangle."""
        pts = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        poly = Polygon2D(pts)
        self.assertFalse(poly.contains_point(np.array([3, 3])))


class TestCircle(unittest.TestCase):
    """Tests for Circle (Ellipse with equal axes)."""

    def test_from_p1_p2(self):
        """Circle from two points: center at midpoint, radius half distance."""
        p1 = np.array([0.0, 0.0])
        p2 = np.array([4.0, 0.0])
        c = Circle.from_p1_p2(p1, p2)
        self.assertAlmostEqual(c.radius, 2.0)
        np.testing.assert_array_almost_equal(c.center, [2.0, 0.0])

    def test_get_sequence_closed(self):
        """get_sequence returns PolyLine2D with num+1 points (closed)."""
        c = Circle(np.array([0.0, 0.0]), 1.0)
        pl = c.get_sequence(num=8)
        self.assertEqual(len(pl), 9)


class TestEllipse(unittest.TestCase):
    """Tests for Ellipse."""

    def test_get_sequence_length(self):
        """get_sequence returns num+1 points."""
        e = Ellipse(np.array([0.0, 0.0]), 2.0, 1.0)
        pl = e.get_sequence(num=10)
        self.assertEqual(len(pl), 11)
