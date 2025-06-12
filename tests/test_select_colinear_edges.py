from sys import path
import pytest

pytest.importorskip("bpy")

import bpy
import add_ons.select_colinear_edges
from add_ons.select_colinear_edges import subdivide_all_faces, select_single_edge, number_of_edges_in_mesh, count_selected_edges, number_of_edges_in_a_subdivided_cube

class TestSelectColinearEdges:
    @classmethod
    def setup_class(cls):
        # Ensure the operator is registered before tests
        if not hasattr(bpy.types, add_ons.select_colinear_edges.OPERATOR_NAME):
            add_ons.select_colinear_edges.register()

    @classmethod
    def teardown_class(cls):
        # Unregister the operator after tests
        if hasattr(bpy.types, add_ons.select_colinear_edges.OPERATOR_NAME):
            add_ons.select_colinear_edges.unregister()

    def test_select_colinear_edges_operator(self, monkeypatch):
        # prepare a sample mesh, a cube with subdivided faces
        n_cuts = 100
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        subdivide_all_faces(obj.data, cuts=n_cuts)
        bpy.ops.object.mode_set(mode="EDIT")
        select_single_edge(obj.data, edge_index=0)

        result = bpy.ops.mesh.select_colinear_edges("INVOKE_DEFAULT")

        n_edges = number_of_edges_in_mesh(obj.data)

        assert result == {"FINISHED"}

        n_selected_edges = count_selected_edges(obj)
        assert n_selected_edges == n_cuts + 1

    def test_select_colinear_edges_benchmark(self, benchmark):
        # prepare a sample mesh, a cube with subdivided faces
        n_cuts = 100
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        subdivide_all_faces(obj.data, cuts=n_cuts)
        bpy.ops.object.mode_set(mode="EDIT")
        select_single_edge(obj.data, edge_index=0)

        # Call the operator. This will in fact call the operator a number of times
        # but once all edges are selected, this will stay constant.
        result = benchmark(bpy.ops.mesh.select_colinear_edges,"INVOKE_DEFAULT")

        # Check result and new location
        assert result == {"FINISHED"}

        n_selected_edges = count_selected_edges(obj)
        assert n_selected_edges == n_cuts + 1
