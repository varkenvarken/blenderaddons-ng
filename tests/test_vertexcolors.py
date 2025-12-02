import pytest

pytest.importorskip("bpy")

import bpy
import add_ons.vertexcolors


class TestVertexcolors:
    @classmethod
    def setup_class(cls):
        # Ensure the operator is registered before tests
        if not hasattr(bpy.types, add_ons.vertexcolors.OPERATOR_NAME):
            add_ons.vertexcolors.register()

    @classmethod
    def teardown_class(cls):
        # Unregister the operator after tests
        if hasattr(bpy.types, add_ons.vertexcolors.OPERATOR_NAME):
            add_ons.vertexcolors.unregister()

    def test_stonework(self):
        bpy.ops.mesh.primitive_cube_add()
        bpy.ops.object.mode_set(mode="VERTEX_PAINT")

        result = bpy.ops.object.random_vertex_colors("INVOKE_DEFAULT")
        assert result == {"FINISHED"}

    def test_stonework_benchmark(self, benchmark):
        result = benchmark(bpy.ops.object.random_vertex_colors, "INVOKE_DEFAULT")

        assert result == {"FINISHED"}
