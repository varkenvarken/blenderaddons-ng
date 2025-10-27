bl_info = {
    "name": "Foreach examples",
    "author": "Michel Anders",
    "version": (0, 0, 20251018121455),
    "blender": (4, 4, 0),
    "location": "Object > Foreach examples",
    "description": "Examples showing foreach_get and foreach_set",
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
from os import environ

try:
    if environ.get("LINE_PROFILE") == "1":
        from line_profiler import profile
    else:  # pragma: no cover
        profile = lambda x: x
except ImportError:  # pragma: no cover
    profile = lambda x: x

from time import time
from typing import Any, Tuple
import bpy
from mathutils import Euler, Vector
from math import pi

from bpy.types import Object, Mesh, Context

import numpy as np
import numpy.typing as npt


@profile
def get_vertex_positions(obj: Object) -> list[Vector]:
    mesh: Mesh = obj.data  # type: ignore
    return [v.co for v in mesh.vertices]


@profile
def get_vertex_positions_np(obj: Object) -> npt.NDArray[np.float32]:
    mesh: Mesh = obj.data  # type: ignore
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coords)
    return coords.reshape(-1, 3)


@profile
def to_world_space(
    verts: npt.NDArray[np.float32], obj: Object
) -> npt.NDArray[np.float32]:
    verts_h = np.concatenate([verts, np.ones((len(verts), 1))], axis=1)
    mat = np.array(obj.matrix_world, dtype=np.float32)
    world_verts = verts_h @ mat.T
    return world_verts[:, :3]


@profile
def get_active_camera_position():
    cam = bpy.context.scene.camera
    if cam is None:
        return None
    return np.array(cam.matrix_world.translation, dtype=np.float32)


@profile
def get_closest_vertex_index_to_camera_naive(
    world_verts: npt.NDArray[np.float32], cam_pos: npt.NDArray[np.float32]
) -> Tuple[int, float | np.floating[Any]]:
    closest_distance = np.inf
    closest_index = -1
    for vertex_index, vertex_pos in enumerate(world_verts):
        direction = vertex_pos - cam_pos
        distance = np.linalg.norm(direction)
        if distance < closest_distance:
            closest_distance = distance
            closest_index = vertex_index
    return closest_index, closest_distance


@profile
def get_closest_vertex_index_to_camera(
    world_verts: npt.NDArray[np.float32], cam_pos: npt.NDArray[np.float32]
) -> Tuple[int, float | np.floating[Any]]:
    dists = np.linalg.norm(world_verts - cam_pos, axis=1)
    i = np.argmin(dists)
    return i, dists[i]  # type: ignore (argmin of an array of floats returns a scalar even though this might not be deduced from the return type)


class OBJECT_OT_foreach_ex(bpy.types.Operator):
    bl_idname = "object.foreach_ex"
    bl_label = "Foreach Example"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        name="Mode",
        description="Choose algorithm to use",
        items=[
            ("NAIVE", "Naive", "Naive Python implementation"),
            ("FOREACH", "Foreach", "Use mesh.foreach_get / foreach_set"),
            ("BROADCAST", "Broadcast", "Use NumPy broadcasting"),
        ],
        default="NAIVE",
    )

    debug: bpy.props.BoolProperty(
        name="Debug",
        description="Enable debug output",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.mode == "OBJECT"
            and context.active_object.type == "MESH"
        )

    @profile  # type: ignore (if line_profiler is available we get a complaint here)
    def do_execute(self, context: Context):
        """Expensive part is moved out of the execute method to allow profiling.

        Note that no profiling is done if line_profiler is not available or
        if the environment variable `LINE_PROFILE` is not set to "1".
        """
        obj: Object = context.active_object  # type: ignore  (the poll function guarantees we have an active object)

        if self.mode == "NAIVE":
            arr = get_vertex_positions(obj)
        else:
            arr = get_vertex_positions_np(obj)

        world_arr = to_world_space(arr, obj)

        if self.mode == "BROADCAST":
            return get_closest_vertex_index_to_camera(world_arr, cam_pos=self.cam_pos)
        else:
            return get_closest_vertex_index_to_camera_naive(
                world_arr, cam_pos=self.cam_pos
            )

    def execute(self, context: Context) -> set[str]:  # type: ignore
        self.cam_pos = get_active_camera_position()
        if self.cam_pos is None:
            self.report({"WARNING"}, "No active camera object")
        else:
            result = self.do_execute(context)
            if self.debug:
                print(result)
        return {"FINISHED"}


OPERATOR_NAME: str = OBJECT_OT_foreach_ex.__name__


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_foreach_ex.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_foreach_ex)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_foreach_ex)


if __name__ == "__main__":  # pragma: no cover
    # this code is for profiling purposes only
    # it is not part of the add-on functionality
    # we simply register the operator, create a cube,
    # and invoke the operator to move the cube along the X axis.
    # if the LINE_PROFILE environment variable is set to "1",
    # the line_profiler will profile the execution of the operator.
    # and print the profiling results.

    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-s",
        "--subdivisions",
        type=int,
        default=5,
        help="number of subdivisions for the cube",
    )
    parser.add_argument(
        "-r",
        "--range",
        action="store_true",
        help="run the operator for a range of subdivision counts (0..subdivisions)",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["NAIVE", "FOREACH", "BROADCAST"],
        default="NAIVE",
        help="Mode to pass to the operator (NAIVE, FOREACH, BROADCAST)",
    )
    args, _ = parser.parse_known_args()
    subdivisions = max(0, int(args.subdivisions))
    cli_mode = args.mode

    register()

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj: Object = bpy.context.active_object  # type: ignore (we just added a primitive so we know for sure active_object is not None)

    # position and orient the default camera
    cam: Object = bpy.context.scene.camera  # type: ignore
    cam.location = 10, 0, 0  # on the x-axis
    cam.rotation_euler = Euler(
        (pi / 2, 0.0, pi / 2), "XYZ"
    )  # pointing towards the origin

    if args.range:
        print("vertices,time")

    for subdivision in range(subdivisions):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.subdivide()
        bpy.ops.object.mode_set(mode="OBJECT")

        if args.range or subdivision == subdivisions - 1:  # always print the last one
            # execute the operator
            start = time()
            result = bpy.ops.object.foreach_ex("INVOKE_DEFAULT", mode=cli_mode)  # type: ignore  (foreach_ex is dynamically added by the register() function, so the typechecker stays unaware)
            seconds = time() - start

            # Print number of vertices after subdivision and the time it took to execute the operator
            num_verts = len(obj.data.vertices)  # type: ignore (we know it is a mesh and that there will be a vertices attribute)
            print(f"{num_verts},{seconds}")

            # this is not a unit test, but at least we know that the operator works
            assert result == {"FINISHED"}

    unregister()

    if (
        profile
        and hasattr(profile, "print_stats")
        and environ.get("LINE_PROFILE") == "1"
    ):
        profile.print_stats()  # type:ignore
