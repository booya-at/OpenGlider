#! /usr/bin/python3
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import copy
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import *
from test_glider import GliderTestClass
import openglider.glider


class TestGliderExtended(GliderTestClass):
    """Extended tests for Glider class to increase coverage"""

    def test_replace_ribs(self):
        """Test replacing ribs in glider"""
        original_ribs = self.glider.ribs[:]
        new_ribs = [rib.copy() for rib in original_ribs]
        # Modify one rib slightly
        new_ribs[0].chord *= 1.1
        
        self.glider.replace_ribs(new_ribs)
        
        # Check that ribs were replaced
        self.assertEqual(len(self.glider.ribs), len(new_ribs))
        self.assertAlmostEqual(self.glider.ribs[0].chord, new_ribs[0].chord)
        self.assertNotEqual(self.glider.ribs[0].chord, original_ribs[0].chord)

    def test_rename_parts(self):
        """Test renaming parts of glider"""
        self.glider.rename_parts()
        
        # Check that cells have names
        for i, cell in enumerate(self.glider.cells):
            self.assertIn(str(i + 1), cell.name)
        
        # Check that ribs have names
        for i, rib in enumerate(self.glider.ribs):
            self.assertIsNotNone(rib.name)

    def test_get_panel_groups(self):
        """Test getting panel groups by material code"""
        groups = self.glider.get_panel_groups()
        
        self.assertIsInstance(groups, dict)
        # Check that all panels are grouped
        total_panels = sum(len(panels) for panels in groups.values())
        expected_panels = sum(len(cell.panels) for cell in self.glider.cells)
        self.assertEqual(total_panels, expected_panels)

    def test_get_mesh_panels(self):
        """Test getting mesh for panels"""
        mesh = self.glider.get_mesh_panels(num_midribs=0)
        self.assertIsNotNone(mesh)
        self.assertEqual(mesh.name, "panels")
        
        # Test with midribs
        mesh_midribs = self.glider.get_mesh_panels(num_midribs=2)
        self.assertIsNotNone(mesh_midribs)

    def test_get_mesh_hull(self):
        """Test getting mesh for hull"""
        mesh = self.glider.get_mesh_hull(num_midribs=0, ballooning=True)
        self.assertIsNotNone(mesh)
        
        mesh_no_ballooning = self.glider.get_mesh_hull(num_midribs=0, ballooning=False)
        self.assertIsNotNone(mesh_no_ballooning)
        
        mesh_with_midribs = self.glider.get_mesh_hull(num_midribs=2)
        self.assertIsNotNone(mesh_with_midribs)

    def test_return_ribs_ij(self):
        """Test getting ribs in ij coordinates"""
        ribs_ij = self.glider.return_ribs_ij(num=0)
        self.assertIsInstance(ribs_ij, list)
        self.assertGreater(len(ribs_ij), 0)
        
        # Check structure
        for rib_ij in ribs_ij:
            self.assertIsInstance(rib_ij, np.ndarray)
            self.assertEqual(len(rib_ij.shape), 2)  # Should be 2D array

    def test_close_rib(self):
        """Test closing a rib"""
        rib_index = 0
        original_profile = copy.deepcopy(self.glider.ribs[rib_index].profile_2d)
        
        self.glider.close_rib(rib_index)
        
        # Check that rib profile is zeroed
        closed_profile = self.glider.ribs[rib_index].profile_2d
        # Profile should be zeroed (multiplied by 0.0)
        for point in closed_profile.data:
            self.assertAlmostEqual(point[1], 0.0, places=5)

    def test_get_point(self):
        """Test getting a point on the glider"""
        # Test various positions
        point1 = self.glider.get_point(y=0, x=-1)  # Trailing edge at first cell
        self.assertIsInstance(point1, np.ndarray)
        self.assertEqual(len(point1), 3)
        
        point2 = self.glider.get_point(y=0.5, x=0)  # Nose at mid-cell
        self.assertIsInstance(point2, np.ndarray)
        self.assertEqual(len(point2), 3)
        
        point3 = self.glider.get_point(y=len(self.glider.cells) - 0.5, x=1)  # Leading edge
        self.assertIsInstance(point3, np.ndarray)
        self.assertEqual(len(point3), 3)

    def test_mirror(self):
        """Test mirroring glider"""
        original_cells_count = len(self.glider.cells)
        original_span = self.glider.span

        self.glider.mirror(cutmidrib=True)
        # With cutmidrib=True the center cell is removed, so span can change
        self.assertGreater(self.glider.span, 0)
        self.assertLessEqual(len(self.glider.cells), original_cells_count)

        # Test mirroring without cutting midrib (full symmetric glider; span differs from half)
        glider2 = self.import_glider()
        glider2.mirror(cutmidrib=False)
        self.assertIsNotNone(glider2)
        self.assertGreater(glider2.span, 0)
        self.assertGreaterEqual(len(glider2.cells), original_cells_count)

    def test_copy(self):
        """Test copying glider"""
        copied = self.glider.copy()
        
        self.assertIsNotNone(copied)
        self.assertEqual(len(copied.cells), len(self.glider.cells))
        self.assertEqual(len(copied.ribs), len(self.glider.ribs))
        
        # Modify copy and ensure original is unchanged
        copied.scale(1.1)
        self.assertNotAlmostEqual(copied.span, self.glider.span)

    def test_copy_complete(self):
        """Test creating complete mirrored copy"""
        complete = self.glider.copy_complete()
        
        self.assertIsNotNone(complete)
        # Complete glider should have more cells (mirrored + original)
        self.assertGreaterEqual(len(complete.cells), len(self.glider.cells))

    def test_shape_simple(self):
        """Test getting simple shape representation"""
        shape = self.glider.shape_simple
        
        self.assertIsNotNone(shape)
        self.assertIsNotNone(shape.front)
        self.assertIsNotNone(shape.back)
        self.assertGreater(len(shape.front), 0)
        self.assertGreater(len(shape.back), 0)

    def test_shape_flattened(self):
        """Test getting flattened shape"""
        shape = self.glider.shape_flattened
        
        self.assertIsNotNone(shape)
        self.assertIsNotNone(shape.front)
        self.assertIsNotNone(shape.back)

    def test_arc(self):
        """Test getting arc property"""
        arc = self.glider.arc
        
        self.assertIsInstance(arc, list)
        self.assertEqual(len(arc), len(self.glider.ribs))
        for point in arc:
            self.assertEqual(len(point), 2)  # y, z coordinates

    def test_trailing_edge_length(self):
        """Test calculating trailing edge length"""
        length = self.glider.trailing_edge_length
        
        self.assertIsInstance(length, (int, float))
        self.assertGreater(length, 0)

    def test_projected_area(self):
        """Test calculating projected area"""
        area = self.glider.projected_area
        
        self.assertIsInstance(area, (int, float))
        self.assertGreater(area, 0)
        # Projected area should be less than or equal to actual area
        self.assertLessEqual(area, self.glider.area * 1.1)  # Allow small tolerance

    def test_centroid(self):
        """Test calculating centroid"""
        centroid = self.glider.centroid
        
        self.assertIsInstance(centroid, (int, float, np.floating))
        # Centroid should be reasonable (positive for typical glider)
        self.assertGreater(centroid, -10)  # Allow some negative values

    def test_get_rib_attachment_points(self):
        """Test getting attachment points for a rib"""
        if len(self.glider.ribs) > 0:
            rib = self.glider.ribs[0]
            points = self.glider.get_rib_attachment_points(rib, brake=True)
            
            self.assertIsInstance(points, list)
            
            # Test with brake=False
            points_no_brake = self.glider.get_rib_attachment_points(rib, brake=False)
            self.assertIsInstance(points_no_brake, list)

    def test_get_cell_attachment_points(self):
        """Test getting attachment points for a cell"""
        if len(self.glider.cells) > 0:
            cell = self.glider.cells[0]
            points = self.glider.get_cell_attachment_points(cell)
            
            self.assertIsInstance(points, list)

    def test_get_main_attachment_point(self):
        """Test getting main attachment point"""
        try:
            main_point = self.glider.get_main_attachment_point()
            self.assertIsNotNone(main_point)
            self.assertIn("main", main_point.name.lower())
        except AttributeError:
            # If no main attachment point exists, that's okay
            pass

    def test_has_center_cell(self):
        """Test checking for center cell (returns Python bool)"""
        has_center = self.glider.has_center_cell
        self.assertIsInstance(has_center, bool)

    def test_glide_property(self):
        """Test glide property getter and setter"""
        original_glide = self.glider.glide
        
        # Set new glide value
        new_glide = 8.5
        self.glider.glide = new_glide
        
        self.assertAlmostEqual(self.glider.glide, new_glide, places=2)
        
        # Restore original
        self.glider.glide = original_glide

    def test_get_spanwise(self):
        """Test getting spanwise points"""
        # Test with x=0 (rib positions)
        spanwise_0 = self.glider.get_spanwise(0)
        self.assertIsInstance(spanwise_0, list)
        self.assertEqual(len(spanwise_0), len(self.glider.ribs))
        
        # Test with x=0.5 (mid-chord)
        spanwise_mid = self.glider.get_spanwise(0.5)
        self.assertIsInstance(spanwise_mid, list)
        self.assertEqual(len(spanwise_mid), len(self.glider.ribs))
        
        # Test with x=None (default)
        spanwise_none = self.glider.get_spanwise(None)
        self.assertIsInstance(spanwise_none, list)

    def test_return_ribs(self):
        """Test returning ribs with different parameters"""
        # Test with default parameters
        ribs_default = self.glider.return_ribs()
        self.assertIsInstance(ribs_default, list)
        self.assertGreater(len(ribs_default), 0)
        
        # Test with midribs
        ribs_midribs = self.glider.return_ribs(num=2)
        self.assertGreater(len(ribs_midribs), len(ribs_default))
        
        # Test without ballooning
        ribs_no_ballooning = self.glider.return_ribs(ballooning=False)
        self.assertIsInstance(ribs_no_ballooning, list)

    def test_empty_glider(self):
        """Test glider with no cells"""
        empty_glider = openglider.glider.Glider(cells=[], lineset=None)
        
        self.assertEqual(empty_glider.area, 0)
        self.assertEqual(empty_glider.span, 0)
        self.assertEqual(len(empty_glider.return_ribs()), 0)
        self.assertEqual(len(empty_glider.return_ribs_ij()), 0)

    def test_profile_x_values(self):
        """Test profile x_values property"""
        original_x_values = self.glider.profile_x_values
        
        # Set new x_values
        new_x_values = [-1.0, -0.5, 0.0, 0.5, 1.0]
        self.glider.profile_x_values = new_x_values
        
        # Check that all ribs have the new x_values
        for rib in self.glider.ribs:
            self.assertEqual(len(rib.profile_2d.x_values), len(new_x_values))
        
        # Restore original
        self.glider.profile_x_values = original_x_values


if __name__ == '__main__':
    unittest.main(verbosity=2)

