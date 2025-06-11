from sys import path
import pytest

pytest.importorskip("bpy")

import bpy
import add_ons.example_simple


class TestExampleSimple:
    @classmethod
    def setup_class(cls):
        # Ensure the operator is registered before tests
        if not hasattr(bpy.types, add_ons.example_simple.OPERATOR_NAME):
            add_ons.example_simple.register()

    @classmethod
    def teardown_class(cls):
        # Unregister the operator after tests
        if hasattr(bpy.types, add_ons.example_simple.OPERATOR_NAME):
            add_ons.example_simple.unregister()

    def test_move_x_operator(self, monkeypatch):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.location.x = 0.0

        # Set the operator amount
        amount = 2.5

        # Call the operator
        result = bpy.ops.object.move_x("INVOKE_DEFAULT", amount=amount)

        # Check result and new location
        assert result == {"FINISHED"}
        assert pytest.approx(obj.location.x) == amount

    def test_move_x_benchmark(self, benchmark):
        bpy.ops.mesh.primitive_cube_add()
        
        obj = bpy.context.active_object
        obj.location.x = 0.0

        # Set the operator amount
        amount = 2.5

        # Call the operator
        result = benchmark(bpy.ops.object.move_x,"INVOKE_DEFAULT", amount=amount)

        # Check result and new location
        assert result == {"FINISHED"}


# This code is a test suite for the example_simple add-on in Blender.
