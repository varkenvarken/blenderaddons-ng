from sys import path
import pytest

pytest.importorskip("bpy")

import bpy
import add_ons.stonework


class TestStonework:
    @classmethod
    def setup_class(cls):
        # Ensure the operator is registered before tests
        if not hasattr(bpy.types, add_ons.stonework.OPERATOR_NAME):
            add_ons.stonework.register()

    @classmethod
    def teardown_class(cls):
        # Unregister the operator after tests
        if hasattr(bpy.types, add_ons.stonework.OPERATOR_NAME):
            add_ons.stonework.unregister()

    def test_stonework(self, monkeypatch):
        result = bpy.ops.object.stonework("INVOKE_DEFAULT")
        assert result == {"FINISHED"}
        
        obj = bpy.context.active_object
        assert obj is not None
        assert obj.type == 'MESH'

    def test_stonework_benchmark(self, benchmark):
        result = benchmark(bpy.ops.object.stonework,"INVOKE_DEFAULT")

        assert result == {"FINISHED"}
