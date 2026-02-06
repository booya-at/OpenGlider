# -*- coding: utf-8 -*-
"""
Unit tests for openglider.utils (cache, colors) – no GUI, no heavy deps.
"""
import unittest
import numpy as np

from openglider.utils.cache import (
    hash_attributes,
    hash_list,
    HashedList,
    recursive_getattr,
)
from openglider.utils.colors import colorwheel, HeatMap


class TestHashAttributes(unittest.TestCase):
    """Tests for cache.hash_attributes and hash_list."""

    def test_hash_list_simple(self):
        """hash_list returns consistent hash for same inputs."""
        a = hash_list(1, 2, 3)
        b = hash_list(1, 2, 3)
        self.assertEqual(a, b)
        self.assertIsInstance(a, int)

    def test_hash_list_different(self):
        """hash_list differs for different inputs."""
        self.assertNotEqual(hash_list(1, 2), hash_list(1, 2, 3))

    def test_hash_attributes_simple_object(self):
        """hash_attributes from object with simple attrs."""
        class Obj:
            x = 1
            y = 2
        o = Obj()
        h = hash_attributes(o, ("x", "y"))
        self.assertIsInstance(h, int)
        o.x = 2
        self.assertNotEqual(h, hash_attributes(o, ("x", "y")))


class TestHashedList(unittest.TestCase):
    """Tests for HashedList (hashable list-like with .data)."""

    def test_len_and_getitem(self):
        """Length and indexing."""
        data = [[0, 0], [1, 0], [1, 1]]
        hl = HashedList(data)
        self.assertEqual(len(hl), 3)
        np.testing.assert_array_almost_equal(hl[0], [0, 0])
        np.testing.assert_array_almost_equal(hl[-1], [1, 1])

    def test_hash_consistent(self):
        """Same data gives same hash."""
        data = [[1, 2], [3, 4]]
        hl1 = HashedList(data)
        hl2 = HashedList(data)
        self.assertEqual(hash(hl1), hash(hl2))

    def test_hash_changes_with_data(self):
        """Changing data changes hash."""
        hl = HashedList([[1, 2], [3, 4]])
        h1 = hash(hl)
        hl.data = [[1, 2], [3, 5]]
        self.assertNotEqual(h1, hash(hl))

    def test_copy(self):
        """copy returns deep copy."""
        data = [[1, 2], [3, 4]]
        hl = HashedList(data)
        cp = hl.copy()
        self.assertIsNot(cp, hl)
        np.testing.assert_array_almost_equal(cp.data, hl.data)


class TestRecursiveGetattr(unittest.TestCase):
    """Tests for recursive_getattr."""

    def test_simple_attr(self):
        """Single attribute."""
        class O:
            a = 1
        self.assertEqual(recursive_getattr(O(), "a"), 1)

    def test_nested_attr(self):
        """Nested attribute a.b."""
        class Inner:
            b = 2
        class O:
            a = Inner()
        self.assertEqual(recursive_getattr(O(), "a.b"), 2)


class TestColorwheel(unittest.TestCase):
    """Tests for utils.colors.colorwheel."""

    def test_colorwheel_length(self):
        """colorwheel(n) returns n RGB tuples."""
        colors = colorwheel(5)
        self.assertEqual(len(colors), 5)
        for c in colors:
            self.assertEqual(len(c), 3)
            self.assertTrue(all(0 <= x <= 255 for x in c))

    def test_colorwheel_values_valid(self):
        """All components in [0, 255]."""
        colors = colorwheel(20)
        for c in colors:
            self.assertTrue(all(0 <= x <= 255 for x in c), msg=c)


class TestHeatMap(unittest.TestCase):
    """Tests for HeatMap (value -> RGB)."""

    def test_heatmap_bounds(self):
        """HeatMap maps min/max to consistent colors."""
        hm = HeatMap(0, 100)
        low = hm(0)
        high = hm(100)
        self.assertEqual(len(low), 3)
        self.assertEqual(len(high), 3)
        self.assertTrue(all(0 <= x <= 255 for x in low))
        self.assertTrue(all(0 <= x <= 255 for x in high))

    def test_heatmap_from_data(self):
        """HeatMap.from_data sets min/max from data."""
        hm = HeatMap.from_data([10.0, 20.0, 30.0])
        self.assertAlmostEqual(hm.min_value, 10.0)
        self.assertAlmostEqual(hm.max_value, 30.0)

    def test_heatmap_clamping(self):
        """Values outside range are clamped to [0,1] then to RGB."""
        hm = HeatMap(0, 1)
        c_below = hm(-0.5)
        c_above = hm(1.5)
        self.assertEqual(len(c_below), 3)
        self.assertEqual(len(c_above), 3)
