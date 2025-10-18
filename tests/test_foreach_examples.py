from sys import path
import pytest

pytest.importorskip("bpy")

import bpy
from mathutils import Euler
from math import pi
import add_ons.foreach_examples


class TestExampleSimple:
    @classmethod
    def setup_class(cls):
        # Ensure the operator is registered before tests
        if not hasattr(bpy.types, add_ons.foreach_examples.OPERATOR_NAME):
            add_ons.foreach_examples.register()

    @classmethod
    def teardown_class(cls):
        # Unregister the operator after tests
        if hasattr(bpy.types, add_ons.foreach_examples.OPERATOR_NAME):
            add_ons.foreach_examples.unregister()

    def test_foreach_ex(self, capsys):
        bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
        obj = bpy.context.active_object
    
        # Subdivide the primitive cube a few times
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        num_verts = len(obj.data.vertices)
        
        assert num_verts == 26

        # position and orient the default camera
        cam = bpy.context.scene.camera
        cam.location = 10,0,0  # on the x-axis
        cam.rotation_euler = Euler((pi/2, 0.0, pi/2), 'XYZ') # pointing towards the origin

        # execute the operator
        result = bpy.ops.object.foreach_ex("INVOKE_DEFAULT", debug=True)

        # Check result and new location
        assert result == {"FINISHED"}
        
        captured = capsys.readouterr()
        assert captured.out == "(23, 9.0)\n"

