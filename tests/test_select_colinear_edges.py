from sys import path
from bpy.types import Object
import pytest

pytest.importorskip("bpy")

import bpy
import add_ons.select_colinear_edges
from add_ons.select_colinear_edges import (
    subdivide_all_faces,
    select_single_edge,
    number_of_edges_in_mesh,
    count_selected_edges,
    number_of_edges_in_a_subdivided_cube,
    colinear_edges,
    select_colinear,
)

from math import radians
import numpy as np


class TestCoreFunctions:
    def test_colinear_edges(self):
        coords = np.array(
            [
                [0, 0, 0],
                [1, 1, 1],
                [2, 2, 2],
                [3, 0, 0],
                [4, 4, 4],
                [5, 5, 5],
            ]
        )
        edges = np.array([[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]])
        angle_threshold = radians(0.1)  # 0.1 degrees
        selected = np.array([True, False, False, False, False])
        result = colinear_edges(selected, edges, coords, angle_threshold)
        expected = np.array([True, True, False, False, True])
        assert np.array_equal(result, expected)

    def test_select_colinear(self):
        # prepare a sample mesh, a cube with subdivided faces
        n_cuts = 100
        bpy.ops.mesh.primitive_cube_add()
        obj: Object = bpy.context.active_object
        subdivide_all_faces(obj.data, cuts=n_cuts)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="EDGE")  # we must be in edge select mode
        select_single_edge(obj.data, edge_index=0)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")
        assert 1 == count_selected_edges(obj)
        
        # we also need to set the angle threshold to guarantee we only select edges colinear to the first edge
        # without the requirment to form a colinear path, we might select parallel edges as well
        # in a unit cube subdivided 100 times, the smallest angle between parallel edges is
        # sin(θ) = 0.01/1 ➞ θ = arcsin(0.01) ≈ 0.6 degrees
        # so we set the angle threshold to 0.1 degrees to get the same result as in the first test
        count = select_colinear(
            obj.data.edges, obj.data.vertices, threshold=radians(0.1)
        )

        # bpy.ops.object.mode_set(mode="EDIT")
        n_selected_edges = count_selected_edges(obj)
        # bpy.ops.object.mode_set(mode="OBJECT")

        assert count == n_cuts + 1
        bpy.ops.object.mode_set(mode="OBJECT")


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
        # this one will select colinear paths, i.e. all edges are connected to the first edge
        # prepare a sample mesh, a cube with subdivided faces
        n_cuts = 100
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        subdivide_all_faces(obj.data, cuts=n_cuts)

        # make sure to match this call with one that switches back to OBJECT mode

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="EDGE")  # we must be in edge select mode
        select_single_edge(obj.data, edge_index=0)

        result = bpy.ops.mesh.select_colinear_edges("INVOKE_DEFAULT")

        assert result == {"FINISHED"}

        n_selected_edges = count_selected_edges(obj)

        assert n_selected_edges == n_cuts + 1

        # next call is needed because we need to return the enviroment to a state similar to where we started
        # bacuse other tests might depend on it

        bpy.ops.object.mode_set(mode="OBJECT")

    def test_select_colinear_edges_2_operator(self, monkeypatch):
        # this one will select all colinear , i.e. regardless whether those edges are connected to the first edge

        # prepare a sample mesh, a cube with subdivided faces
        n_cuts = 100
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        subdivide_all_faces(obj.data, cuts=n_cuts)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="EDGE")  # we must be in edge select mode
        select_single_edge(obj.data, edge_index=0)

        # we also need to set the angle threshold to gurantee we only select edges colinear to the first edge
        # without the requirment to form a colinear path, we might select parallel edges as well
        # in a unit cube subdivided 100 times, the smallest angle between parallel edges is
        # sin(θ) = 0.01/1 ➞ θ = arcsin(0.01) ≈ 0.6 degrees
        # so we set the angle threshold to 0.1 degrees to get the same result as in the first test
        result = bpy.ops.mesh.select_colinear_edges(
            "INVOKE_DEFAULT", only_colinear_paths=False, angle_threshold=radians(0.1)
        )

        assert result == {"FINISHED"}

        n_selected_edges = count_selected_edges(obj)
        assert n_selected_edges == n_cuts + 1
        bpy.ops.object.mode_set(mode="OBJECT")

    def helper(self, obj):
        result = bpy.ops.mesh.select_colinear_edges(
            "INVOKE_DEFAULT", only_colinear_paths=False, angle_threshold=radians(0.1)
        )
        select_single_edge(obj.data, edge_index=0)
        return result

    def test_select_colinear_edges_benchmark(self, benchmark):
        # prepare a sample mesh, a cube with subdivided faces
        n_cuts = 100
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        subdivide_all_faces(obj.data, cuts=n_cuts)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="EDGE")  # we must be in edge select mode
        select_single_edge(obj.data, edge_index=0)

        # the helper will be called multiple times by the benchmark
        # the help will call the operator and then reset the selection
        # this means deselecting all but one edge is incorparted in the benchmark but that's what it is
        result = benchmark(self.helper, obj)

        # Check result and new location
        assert result == {"FINISHED"}

        bpy.ops.object.mode_set(mode="OBJECT")
