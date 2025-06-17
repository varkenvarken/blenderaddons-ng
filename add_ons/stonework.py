bl_info = {
    "name": "Simple Stonework Generator",
    "author": "Your Name",
    "version": (0, 0, 20250611074806),
    "blender": (4, 4, 0),
    "location": "Object > Stonework",
    "description": "Create a stonework pattern with random rows of stones",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Object",
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
import random
from mathutils import Vector

# TODO: add tests
# TODO: prevent last stone in a row from being too narrow
# TODO: change the beveling: generate the gap between the stones directly (currently we get inconsistent widths because of overlap clamping)
# TODO: add a variable stone height


def stonework(
    wall_height=2.0,
    wall_width=2.0,
    stone_height=1,
    minimum_stone_width=0.5,
    extra_stone_width=0.5,
    first_stone_width=0.5,
):
    from dataclasses import dataclass
    import random

    @dataclass
    class Face:
        row: int
        column: int
        x1: float
        y1: float
        x2: float
        y2: float

    @dataclass
    class Vertex:
        x: float
        y: float

    class Polygon(list): ...

    def in_range(positions, a, b):
        """
        return a list values that lie between a and b (inclusive)
        """
        r = list()
        a -= 1e-6
        b += 1e-6
        for p in positions:
            if p >= a and p <= b:
                r.append(p)
        return r

    # create a list of rectangular faces, going left to right, bottom to top
    faces = list()
    y = 0.0
    row_index = 0
    while y < wall_height:
        x = 0.0
        column_index = 0
        while x < wall_width:
            stone_width = (
                first_stone_width
                if column_index == 0 and row_index % 2 == 0
                else minimum_stone_width
            ) + random.random() * extra_stone_width
            right_edge = min(x + stone_width, wall_width)
            top_edge = min(y + stone_height, wall_height)
            face = Face(
                row=row_index,
                column=column_index,
                x1=x,
                x2=right_edge,
                y1=y,
                y2=top_edge,
            )
            faces.append(face)
            x += stone_width
            column_index += 1
        y += stone_height
        row_index += 1

    # collect all x values for each height, make them unique and sort them in ascending order
    from collections import defaultdict

    rows_of_x_values = defaultdict(
        set
    )  # the set will keep our collection of values unique
    for face in faces:
        rows_of_x_values[face.row].add(face.x1)
        rows_of_x_values[face.row].add(face.x2)
        rows_of_x_values[face.row + 1].add(face.x1)
        rows_of_x_values[face.row + 1].add(face.x2)

    # converts all sets of x values to sorted lists
    for row_index, values in rows_of_x_values.items():
        rows_of_x_values[row_index] = list(
            values
        )  # type:ignore (we convert to a list and pylance will complain)
        rows_of_x_values[row_index].sort()  # type:ignore

    # convert the rectangles with four vertices to polygons that may have more than four
    # if verts of other rectangles coincide with an edge
    unique_vertices = {}
    new_vertex_index = 0
    polygons = []
    for face in faces:
        polygon = Polygon()
        polygons.append(polygon)

        for lower_x in in_range(rows_of_x_values[face.row], face.x1, face.x2):
            vertex = (lower_x, face.y1)
            if vertex in unique_vertices:
                vertex_index = unique_vertices[vertex]
            else:
                unique_vertices[vertex] = new_vertex_index
                vertex_index = new_vertex_index
                new_vertex_index += 1
            polygon.append(vertex_index)

        # upper stretch of vertices in reverse order to guarantee counter clockwise winding for all vertices of the polygon
        for upper_x in reversed(
            list(in_range(rows_of_x_values[face.row + 1], face.x1, face.x2))
        ):
            vertex = (upper_x, face.y2)
            if vertex in unique_vertices:
                vertex_index = unique_vertices[vertex]
            else:
                unique_vertices[vertex] = new_vertex_index
                vertex_index = new_vertex_index
                new_vertex_index += 1
            polygon.append(vertex_index)

    # invert the mapping from vertex coordinates --> index to index --> vertex coordinates
    unique_vertices = {v: k for k, v in unique_vertices.items()}

    # # print a list of coordinates and indices. Just so we can do some checks in a spreadheet
    # for p in polygons:
    #     for vertex in p:
    #         vert = unique_vertices[vertex]
    #         print(f"{vert[0]:.4f},{vert[1]:.4f},{vertex}")
    return polygons, unique_vertices


class OBJECT_OT_stonework(bpy.types.Operator):
    bl_idname = "object.stonework"
    bl_label = "Add a wall of random stones"
    bl_options = {"REGISTER", "UNDO"}

    wall_width: bpy.props.FloatProperty(
        name="Plane Width",
        default=4.0,
        min=0.1,
        description="Total width of the wall",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    wall_height: bpy.props.FloatProperty(
        name="Plane Height",
        default=2.0,
        min=0.1,
        description="Total height of the wall",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    stone_height: bpy.props.FloatProperty(
        name="Row Height",
        default=0.5,
        min=0.01,
        description="Height of each row of stones",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    minimum_stone_width: bpy.props.FloatProperty(
        name="Min Stone Width",
        default=0.3,
        min=0.001,
        description="Minimum width of a stone",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    extra_stone_width: bpy.props.FloatProperty(
        name="Extra Stone Width",
        default=1.0,
        min=0.0,
        description="Random width added to each individual stone",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    minimum_stone_width_of_first_stone: bpy.props.FloatProperty(
        name="Min First Width",
        default=0.3,
        min=0.001,
        description="Minimum width of the stone on uneven rows (1st, 3rd, etc.)",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    merge_threshold: bpy.props.FloatProperty(
        name="Merge Threshold",
        default=1e-6,
        min=1e-8,
        description="Distance threshold for merging vertices",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    gap_width: bpy.props.FloatProperty(
        name="Gap Width",
        default=0.05,
        min=0.0,
        description="Width of the gap between the stones",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    gap_depth: bpy.props.FloatProperty(
        name="Gap Depth",
        default=-0.02,
        description="Depth of the gap between the stones",
        subtype="DISTANCE",
        unit="LENGTH",
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        default=0,
        description="Random seed for reproducibility; change to get different results",
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    @profile  # type: ignore (if line_profiler is available)
    def do_execute(self, context) -> None:
        """Expensive part is moved out of the execute method to allow profiling.

        Note that no profiling is done if line_profiler is not available or
        if the environment variable `LINE_PROFILE` is not set to "1".
        """
        mesh = bpy.data.meshes.new("RandomRowPlane")
        obj = bpy.data.objects.new("RandomRowPlane", mesh)
        context.collection.objects.link(obj)
        bm = bmesh.new()

        polygons, verts = stonework(
            wall_height=self.wall_height,
            wall_width=self.wall_width,
            stone_height=self.stone_height,
            minimum_stone_width=self.minimum_stone_width,
            extra_stone_width=self.extra_stone_width,
            first_stone_width=self.minimum_stone_width_of_first_stone,
        )

        indices = list(verts.keys())
        indices.sort()
        bm_verts = [
            bm.verts.new(Vector((verts[i][0], verts[i][1], 0.0))) for i in indices
        ]
        bm.verts.index_update()
        bm.verts.ensure_lookup_table()

        for p in polygons:
            bm.faces.new([bm_verts[i] for i in p])

        bm.to_mesh(mesh)
        bm.free()

        # Switch to edit mode and edge select mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="EDGE")

        # Deselect all edges first
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        for e in bm.edges:
            e.select = False

        # Select all non-boundary edges
        for e in bm.edges:
            if not e.is_boundary:
                e.select = True

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

        affected = bmesh.ops.bevel(
            bm,
            geom=[e for e in bm.edges if e.select],
            offset=self.gap_width,
            offset_type="WIDTH",
            profile_type="SUPERELLIPSE",
            segments=1,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
            material=-1,
            loop_slide=False,
            mark_seam=False,
            mark_sharp=False,
            harden_normals=False,
            face_strength_mode="NONE",
            miter_outer="SHARP",
            miter_inner="SHARP",
            spread=0,
            # custom_profile=None,
            vmesh_method="ADJ",
        )

        if abs(self.gap_depth) > 1e-5:
            # Select all faces first
            for f in bm.faces:
                f.select_set(True)

            # Deselect all bevel faces
            for f in affected["faces"]:
                f.select_set(False)

            extruded = bmesh.ops.extrude_discrete_faces(
                bm, faces=[f for f in bm.faces if f.select]
            )

            for f in extruded["faces"]:
                for v in f.verts:
                    v.co.z += self.gap_depth

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=True)

        bpy.ops.object.mode_set(mode="OBJECT")

    def execute(self, context) -> set[str]:  # type: ignore
        """Move the active object along the X axis."""
        random.seed(self.seed)
        self.do_execute(context)
        return {"FINISHED"}


OPERATOR_NAME: str = OBJECT_OT_stonework.__name__


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_stonework.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_stonework)
    bpy.types.VIEW3D_MT_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_stonework)


if __name__ == "__main__":  # pragma: no cover
    # this code is for profiling purposes only
    # it is not part of the add-on functionality
    # we simply register the operator, create a cube,
    # and invoke the operator to move the cube along the X axis.
    # if the LINE_PROFILE environment variable is set to "1",
    # the line_profiler will profile the execution of the operator.
    # and print the profiling results.

    register()

    result = bpy.ops.object.stonework("INVOKE_DEFAULT")
    # this is not a unit test, but at least we know that the operator works
    assert result == {"FINISHED"}

    unregister()

    if (
        profile
        and hasattr(profile, "print_stats")
        and environ.get("LINE_PROFILE") == "1"
    ):
        profile.print_stats()  # type:ignore
