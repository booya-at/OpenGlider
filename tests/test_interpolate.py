# -*- coding: utf-8 -*-
"""
Unit tests for openglider.vector.interpolate.Interpolation.
"""
import unittest
import numpy as np

from openglider.vector import Interpolation


class TestInterpolation(unittest.TestCase):
    """Tests for piecewise linear interpolation (x -> y)."""

    def test_linear_in_range(self):
        """Interpolation between two points is linear."""
        data = [[0.0, 0.0], [1.0, 2.0]]
        interp = Interpolation(data, extrapolate=False)
        self.assertAlmostEqual(interp(0.0), 0.0)
        self.assertAlmostEqual(interp(1.0), 2.0)
        self.assertAlmostEqual(interp(0.5), 1.0)

    def test_linear_multiple_segments(self):
        """Multiple segments: correct value in each segment."""
        data = [[0, 0], [1, 10], [2, 20], [3, 5]]
        interp = Interpolation(data, extrapolate=False)
        self.assertAlmostEqual(interp(0.0), 0.0)
        self.assertAlmostEqual(interp(1.0), 10.0)
        self.assertAlmostEqual(interp(1.5), 15.0)
        self.assertAlmostEqual(interp(2.5), 12.5)

    def test_extrapolate_false_raises_out_of_range(self):
        """Without extrapolation, x outside [x0, x_end] raises."""
        data = [[0.0, 0.0], [1.0, 1.0]]
        interp = Interpolation(data, extrapolate=False)
        with self.assertRaises(Exception):
            interp(-0.1)
        with self.assertRaises(Exception):
            interp(1.1)

    def test_extrapolate_true_extends_linear(self):
        """With extrapolation, values outside range extend linearly."""
        data = [[0.0, 0.0], [1.0, 2.0]]
        interp = Interpolation(data, extrapolate=True)
        self.assertAlmostEqual(interp(-1.0), -2.0)
        self.assertAlmostEqual(interp(2.0), 4.0)

    def test_extrapolate_true_at_last_segment(self):
        """Extrapolate=True allows query at and beyond last point (last-segment slope)."""
        data = [[0, 0], [1, 1], [2, 3]]
        interp = Interpolation(data, extrapolate=True)
        self.assertAlmostEqual(interp(2.0), 3.0)
        # Last segment (1,1)->(2,3) has slope 2, so at x=3: y = 3 + 2*(3-2) = 5
        self.assertAlmostEqual(interp(3.0), 5.0)

    def test_single_interval_boundaries(self):
        """Boundary values match data exactly."""
        data = [[0.0, 5.0], [10.0, 15.0]]
        interp = Interpolation(data, extrapolate=False)
        self.assertAlmostEqual(interp(0.0), 5.0)
        self.assertAlmostEqual(interp(10.0), 15.0)
