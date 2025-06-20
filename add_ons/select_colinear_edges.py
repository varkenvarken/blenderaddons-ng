bl_info = {
    "name": "Select Colinear Edges",
    "author": "michel.anders, GitHub Copilot",
    "version": (1, 1, 20250615085624),
    "blender": (4, 4, 0),
    "location": "View3D > Select > Select Similar > Colinear Edges",
    "description": "Select all edges colinear with any currently selected edge, optionally only along colinear paths",
    "category": "Mesh",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
}

# import line_profiler if available or create a no-op decorator
# note that profiling is only done if the environment variable
# `LINE_PROFILE` is set to "1"
# and the line_profiler package is installed
# otherwise, the operator will run without profiling
try:
    from line_profiler import profile
except ImportError:  # pragma: no cover
    profile = lambda x: x

from os import environ

import bpy
import bmesh
from mathutils import Vector
from math import radians

import numpy as np

@profile
def select_colinear(edges, vertices, threshold):
    n_edges = len(edges)
    n_vertices = len(vertices)
    indices = np.empty(2 * n_edges, dtype=int)
    coords = np.empty(3 * n_vertices, dtype=float)
    selected = np.zeros(n_edges, dtype=bool)
    edges.foreach_get("vertices", indices)
    edges.foreach_get("select", selected)
    vertices.foreach_get("co", coords)
    coords = coords.reshape((n_vertices, 3))
    indices = indices.reshape((n_edges, 2))

    colinear = colinear_edges(selected, indices, coords, threshold)
    edges.foreach_set("select", colinear)
    return np.count_nonzero(colinear)

@profile
def colinear_edges(selected: np.ndarray, indices, coords, threshold):
    colinear = np.zeros_like(selected)

    # calculate direction vectors for each edge
    edge_dirs = coords[indices[:, 1]] - coords[indices[:, 0]]
    edge_dirs = edge_dirs / np.linalg.norm(edge_dirs, axis=1)[:, np.newaxis]

    for e in selected.nonzero()[0]:
        # get the direction vector of the selected edge
        dir1 = edge_dirs[e]
        # check all other edges for colinearity
        angles = np.arccos(np.clip(np.dot(dir1, edge_dirs.T), -1.0, 1.0))
        parallel = (angles < threshold) | (np.abs(angles - np.pi) < threshold)
        v1 = coords[indices[e, 0]]
        w1 = coords[indices[:, 0]]
        # vector between start points
        between = w1 - v1
        # if the vector between start points is zero, they share a vertex, so colinear
        between_length = np.linalg.norm(between, axis=1)
        connected = between_length < 1e-6
        angles_between = np.abs(
            np.arccos(
                np.clip(
                    np.dot(dir1, (between / between_length[:, np.newaxis]).T), -1.0, 1.0
                )
            )
        )
        bparallel = (angles_between < threshold) | (
            np.abs(angles_between - np.pi) < threshold
        )
        # colinear if they are parallel and either share a vertex or the angle between the direction vector and the vector between start points is less than the threshold
        colinear |= (connected | bparallel) & parallel

    return colinear


class MESH_OT_select_colinear_edges(bpy.types.Operator):
    """Select all edges colinear with any currently selected edge, optionally only along colinear paths"""

    bl_idname = "mesh.select_colinear_edges"
    bl_label = "Colinear Edges"
    bl_options = {"REGISTER", "UNDO"}

    angle_threshold: bpy.props.FloatProperty(
        name="Angle Threshold",
        description="Maximum angle (degrees) to consider edges colinear",
        default=radians(1),
        min=0.0,
        max=radians(90),
        soft_max=radians(10),
        subtype="ANGLE",
    )

    only_colinear_paths: bpy.props.BoolProperty(
        name="Only Colinear Paths",
        description="Only select edges connected via colinear paths from the originally selected edges",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and context.mode == "EDIT_MESH"

    def execute(self, context):
        return self.do_execute(context)

    @profile
    def do_execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object

        threshold_rad = self.angle_threshold

        @profile
        def edge_dir(edge):
            v1, v2 = edge.verts
            return (v2.co - v1.co).normalized()

        @profile
        def are_colinear(e1, e2):
            # Check if direction vectors are parallel
            v1, v2 = e1.verts
            dir1 = v2.co - v1.co  # .normalized()
            # guard against zero length edges
            # if dir1.length < 1e-6:
            #     return False
            v1, v2 = e2.verts
            dir2 = v2.co - v1.co  # .normalized()
            # if dir2.length < 1e-6:
            #     return False
            angle = dir1.angle(dir2, 10)
            # if angle is None:
            #     return False
            if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
                return False
            # Check if the vector between their start points is also parallel to the direction
            v1 = e1.verts[0].co
            w1 = e2.verts[0].co
            between = w1 - v1
            # If between is zero vector, they share a vertex, so colinear
            if between.length < 1e-6:
                return True
            between_dir = between.normalized()
            angle2 = dir1.angle(between_dir)
            return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad

        if self.only_colinear_paths:
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()

            # Find all originally selected edges
            original_selected_edges = [e for e in bm.edges if e.select]
            if not original_selected_edges:
                self.report({"WARNING"}, "No edges selected")
                return {"CANCELLED"}

            # Deselect all edges first
            for e in bm.edges:
                e.select = False

            visited = set()
            queue = []
            for e in original_selected_edges:
                queue.append(e)
                visited.add(e)

            while queue:
                current_edge = queue.pop(0)
                current_edge.select = True
                for v in current_edge.verts:
                    for neighbor in v.link_edges:
                        if neighbor is current_edge or neighbor in visited:
                            continue
                        if are_colinear(current_edge, neighbor):
                            queue.append(neighbor)
                            visited.add(neighbor)
            bmesh.update_edit_mesh(obj.data)
        else:
            # for e in bm.edges:
            #     for sel_edge in original_selected_edges:
            #         if are_colinear(sel_edge, e):
            #             e.select = True
            #             break
            # bmesh.update_edit_mesh(obj.data)
            bpy.ops.object.mode_set(mode="OBJECT")
            select_colinear(obj.data.edges, obj.data.vertices, self.angle_threshold)
            bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


OPERATOR_NAME: str = MESH_OT_select_colinear_edges.__name__


def menu_func(self, context):
    self.layout.operator(MESH_OT_select_colinear_edges.bl_idname, text="Colinear Edges")


def register():
    bpy.utils.register_class(MESH_OT_select_colinear_edges)
    bpy.types.VIEW3D_MT_edit_mesh_select_similar.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_select_similar.remove(menu_func)
    bpy.utils.unregister_class(MESH_OT_select_colinear_edges)


# helper functions, can be used by the testing scripts as well
import bmesh


def subdivide_all_faces(mesh_obj: bpy.types.Mesh, cuts=1) -> None:
    """
    Subdivide all faces of the given mesh object.

    :param mesh_obj: A Blender mesh object (bpy.types.Mesh)
    :param cuts: Number of cuts for subdivision (default: 1)
    """

    bm = bmesh.new()
    bm.from_mesh(mesh_obj)
    # subdivide all faces (while ensuring we pass each edge only once)
    faces = [f for f in bm.faces]
    bmesh.ops.subdivide_edges(
        bm,
        edges=list(set(e for f in faces for e in f.edges)),
        cuts=cuts,
        use_grid_fill=True,
    )
    bm.to_mesh(mesh_obj)
    bm.free()  # free and prevent further access


def select_single_edge(mesh_obj: bpy.types.Mesh, edge_index=0) -> None:
    """
    Select a single edge in the given mesh object by index.
    Assumes the object is in edit mode.

    :param mesh_obj: A Blender mesh object (bpy.types.Mesh)
    :param edge_index: Index of the edge to select (default: 0)
    """
    import bmesh

    bm = bmesh.from_edit_mesh(mesh_obj)
    bm.edges.ensure_lookup_table()

    # Deselect all edges first
    for e in bm.edges:
        e.select = False

    # Select the specified edge
    if 0 <= edge_index < len(bm.edges):
        bm.edges[edge_index].select = True

    bm.select_flush_mode()

    bmesh.update_edit_mesh(mesh_obj)


def count_selected_edges(mesh_obj: bpy.types.Mesh) -> int:
    """
    Return the number of selected edges in the given mesh object.
    Assumes the object is in edit mode.

    :param mesh_obj: A Blender mesh object (bpy.types.Object)
    :return: Number of selected edges (int)
    """
    import bmesh

    bm = bmesh.from_edit_mesh(mesh_obj.data)
    bm.edges.ensure_lookup_table()  # i don´t think this is necessary just to count
    return sum(1 for e in bm.edges if e.select)


def number_of_edges_in_a_subdivided_cube(cuts: int = 1) -> int:
    # this reads:
    # 6 faces * 2 directions (i.e. horizontal and vertical)
    # * number of cuts * (number of cuts + 1)
    # + 12 original edges (the edges of the cube) * (cuts + 1)
    #
    # 1 -> 48
    # 2 -> 108
    # 3 -> 192
    # ...

    return 6 * 2 * (cuts * (cuts + 1)) + 12 * (cuts + 1)


def number_of_edges_in_mesh(mesh_obj: bpy.types.Mesh) -> int:
    """
    Return the number of edges in the given mesh object.

    :param mesh_obj: A Blender mesh object (bpy.types.Mesh)
    :return: Number of edges (int)
    """
    return len(mesh_obj.edges)


if __name__ == "__main__":  # pragma: no cover
    # this code is for profiling purposes only
    # it is not part of the add-on functionality
    # we simply register the operator, create a subdivided cube,
    # and invoke the operator.
    # if the LINE_PROFILE environment variable is set to "1",
    # the line_profiler will profile the execution of the operator.
    # and print the profiling results.

    register()

    # prepare a sample mesh, a cube with subdivided faces
    n_cuts = 500
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    subdivide_all_faces(obj.data, cuts=n_cuts)
    bpy.ops.object.mode_set(mode="EDIT")
    select_single_edge(obj.data, edge_index=0)

    # selecting parallel edges is heaview than selecting colinear paths and that is what we use here for profiling
    result = bpy.ops.mesh.select_colinear_edges(
        "INVOKE_DEFAULT", only_colinear_paths=False, angle_threshold=radians(0.1)
    )

    n_edges = number_of_edges_in_mesh(obj.data)

    # this is not a unit test, but at least we know that the operator works
    assert result == {"FINISHED"}

    unregister()

    if (
        profile
        and hasattr(profile, "print_stats")
        and environ.get("LINE_PROFILE") == "1"
    ):
        profile.print_stats()  # type:ignore
