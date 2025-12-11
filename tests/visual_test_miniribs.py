import sys
import os
import unittest
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openglider
from openglider.glider.rib import MiniRib
from openglider.glider import ParametricGlider
from openglider.airfoil import Profile2D
import openglider.graphics as Graph
from openglider.utils.distribution import Distribution


class TestMiniRibsVisualization(unittest.TestCase):
    def setUp(self):
        # Create a basic glider configuration
        # This mirrors minimal setup for a ParametricGlider
        from openglider.glider.parametric.shape import ParametricShape
        from openglider.glider.parametric.arc import ArcCurve

        shape = ParametricShape(
            span=10, aspect_ratio=5, taper=0.7, sweep=0.5, area=25
        )
        arc = ArcCurve(width=0.8, height=0.4, flat=0.6)
        
        # Need some basic profiles
        # Use simple profile for testing
        x = np.linspace(1, 0, 50)
        y = 0.1 * 4 * x * (1-x) # Parabolic arc
        profile_data = np.column_stack((x, y))
        p1 = Profile2D(profile_data)
        
        self.glider = ParametricGlider(
            shape=shape,
            arc=arc,
            aoa=Distribution.from_linear_distribution(0),
            profiles=[p1],
            profile_merge_curve=Distribution.from_linear_distribution(0),
            balloonings=[],
            ballooning_merge_curve=Distribution.from_linear_distribution(0),
            lineset=None,
            speed=10,
            glide=10,
            zrot=None
        )
        
    def test_visualize_miniribs(self):
        # Add miniribs to the parametric glider configuration
        minirib_config = {
            "yvalue": 0.5,      # Middle of current cell section
            "front_cut": 0.8,   # Starts at 80% chord
            "back_cut": 1.0,    # Ends at 100% chord
            "cells": [0, 1]     # Apply to first few cells
        }
        
        self.glider.elements["miniribs"] = [minirib_config]
        
        # Generate the 3D glider instance
        glider3d = self.glider.get_glider_3d()
        
        # Collect geometry for visualization
        geometries = []
        
        # Add main ribs (black)
        for rib in glider3d.ribs:
            geometries.append(Graph.Line(rib.profile_3d.data, width=2, colour=Graph.Black))
            
        # Add miniribs (red)
        for cell in glider3d.cells:
            for mr in cell.miniribs:
                mr_3d = mr.get_3d(cell)
                geometries.append(Graph.Line(mr_3d.data, width=2, colour=Graph.Red))
                print(f"Added minirib for cell {cell.name} at y={mr.y_value}")

        print(f"Total geometry elements: {len(geometries)}")
        
        # In a real visual environment we would show this, here we just verify generation
        if len(geometries) > len(glider3d.ribs):
            print("SUCCESS: Miniribs generated geometry.")
        else:
            self.fail("No minirib geometry generated.")
        

if __name__ == "__main__":
    unittest.main()
