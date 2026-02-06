# -*- coding: utf-8 -*-
"""
Unit tests for openglider.vector.transformation (Transformation, Rotation, Reflection, Scale, Translation).
"""
import unittest
import numpy as np

from openglider.vector.transformation import (
    Transformation,
    Rotation,
    Reflection,
    Scale,
    Translation,
)


class TestTransformation(unittest.TestCase):
    """Tests for 4x4 Transformation base and apply."""

    def test_apply_3d(self):
        """apply maps 3D points with rotation + translation."""
        # Identity-like: scale 1, no translation
        mat = np.eye(4)
        mat[3, :3] = [1, 2, 3]
        t = Transformation(mat)
        vec = np.array([[0, 0, 0]])
        out = t.apply(vec)
        np.testing.assert_array_almost_equal(out[0], [1, 2, 3])

    def test_call_3d(self):
        """__call__ maps single 3D vector."""
        mat = np.eye(4)
        mat[3, :3] = [0, 0, 0]
        t = Transformation(mat)
        out = t(np.array([1.0, 0.0, 0.0]))
        np.testing.assert_array_almost_equal(out, [1, 0, 0])


class TestRotation(unittest.TestCase):
    """Tests for Rotation (axis-angle)."""

    def test_rotation_z_90(self):
        """90° around z: (1,0,0) -> (0,1,0)."""
        r = Rotation(np.pi / 2, np.array([0, 0, 1]))
        pt = np.array([1.0, 0.0, 0.0])
        out = r(pt)
        np.testing.assert_array_almost_equal(out, [0, 1, 0], decimal=5)

    def test_rotation_identity(self):
        """Angle 0 gives identity."""
        r = Rotation(0, np.array([1, 0, 0]))
        pt = np.array([1.0, 2.0, 3.0])
        np.testing.assert_array_almost_equal(r(pt), pt)


class TestReflection(unittest.TestCase):
    """Tests for Reflection (mirror in plane)."""

    def test_reflection_y_axis(self):
        """Reflect in y=0: (1,1,0) -> (1,-1,0)."""
        ref = Reflection(np.array([0, 1, 0]))  # mirror normal
        pt = np.array([1.0, 1.0, 0.0])
        out = ref(pt)
        np.testing.assert_array_almost_equal(out, [1, -1, 0], decimal=5)


class TestScale(unittest.TestCase):
    """Tests for Scale transformation."""

    def test_scale_uniform(self):
        """Uniform scale 2."""
        s = Scale(2.0)
        pt = np.array([1.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(s(pt), [2, 2, 2])

    def test_scale_vector(self):
        """Per-axis scale."""
        s = Scale(np.array([2.0, 1.0, 3.0]))
        pt = np.array([1.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(s(pt), [2, 1, 3])


class TestTranslation(unittest.TestCase):
    """Tests for Translation."""

    def test_translation(self):
        """Translation adds vector."""
        t = Translation(np.array([1.0, 2.0, 3.0]))
        pt = np.array([0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(t(pt), [1, 2, 3])

    def test_translation_default(self):
        """Default translation is zero."""
        t = Translation()
        pt = np.array([1.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(t(pt), [1, 1, 1])
