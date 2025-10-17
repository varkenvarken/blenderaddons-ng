bl_info = {
    "name": "Foreach examples",
    "author": "Michel Anders",
    "version": (0, 0, 20251017133206),
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
try:
    from line_profiler import profile
except ImportError:  # pragma: no cover
    profile = lambda x: x

from os import environ
import bpy
from mathutils import Euler
from math import pi

from bpy.types import Object, Context

import numpy as np

@profile
def ray_intersect_triangles(vertices, triangles, ray):
    """
    Find the closest intersection of a ray with a mesh of triangles.

    This is a very straight forward (naive) implementation.

    Parameters:
        vertices: np.ndarray, shape (m, 3)
            3D coordinates of mesh vertices.
        triangles: np.ndarray, shape (3, n)
            Each column contains indices into vertices, defining one triangle.
        ray: np.ndarray, shape (2, 3)
            ray[0]: origin, ray[1]: direction (not necessarily normalized)

    Returns:
        tuple: (triangle_index, distance) of closest hit, or None if no intersection.
    """
    origin = ray[0]
    direction = ray[1]
    closest_dist = np.inf
    closest_idx = None

    for idx in range(triangles.shape[1]):
        v0, v1, v2 = vertices[triangles[:, idx]]
        # edges
        edge1 = v1 - v0
        edge2 = v2 - v0
        h = np.cross(direction, edge2)
        a = np.dot(edge1, h)
        if abs(a) < 1e-8:  # parallel
            continue
        f = 1.0 / a
        s = origin - v0
        u = f * np.dot(s, h)
        if u < 0.0 or u > 1.0:
            continue
        q = np.cross(s, edge1)
        v = f * np.dot(direction, q)
        if v < 0.0 or u + v > 1.0:
            continue
        t = f * np.dot(edge2, q)
        if t > 1e-8 and t < closest_dist:  # intersection and closer
            closest_dist = t
            closest_idx = idx

    if closest_idx is not None:
        return closest_idx, closest_dist
    else:
        return None

@profile    
def get_vertex_positions_np(obj):
    if not obj or obj.type != 'MESH':
        return None
    mesh = obj.data
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coords)
    return coords.reshape(-1, 3)

@profile
def to_world_space(verts, obj):
    if obj is None:
        return None
    verts_h = np.concatenate([verts, np.ones((verts.shape[0], 1))], axis=1)
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
def get_closest_vertex_index_to_camera(world_verts, cam_pos):
    if cam_pos is None or world_verts is None:
        return None
    dists = np.linalg.norm(world_verts - cam_pos, axis=1)
    i = np.argmin(dists)
    return i, dists[i]

class OBJECT_OT_foreach_ex(bpy.types.Operator):
    bl_idname = "object.foreach_ex"
    bl_label = "Foreach Example"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode == "OBJECT"

    @profile  # type: ignore (if line_profiler is available)
    def do_execute(self, context: Context) -> None:
        """Expensive part is moved out of the execute method to allow profiling.

        Note that no profiling is done if line_profiler is not available or
        if the environment variable `LINE_PROFILE` is not set to "1".
        """
        obj: Object | None = context.active_object
        arr = get_vertex_positions_np(obj)
        if arr is not None:
            world_arr = to_world_space(arr, obj)
            cam_pos = get_active_camera_position()
            if cam_pos is not None:
                return get_closest_vertex_index_to_camera(world_arr, cam_pos=cam_pos)
            else:
                self.report({'WARNING'}, "No active camera object")    
        else:
            self.report({'WARNING'}, "No active mesh object")
    
    def execute(self, context: Context) -> set[str]:  # type: ignore
        print(self.do_execute(context))
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

    register()

    bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
    obj = bpy.context.active_object
 
    # Subdivide the primitive cube a few times
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=40)
    bpy.ops.mesh.subdivide(number_cuts=40)  # this gets us to about 17 million verts
    bpy.ops.object.mode_set(mode='OBJECT')
    # Print number of vertices after subdivision
    num_verts = len(obj.data.vertices)
    print(f"{num_verts=}")
    # position and orient the default camera
    cam = bpy.context.scene.camera
    cam.location = 10,0,0  # on the x-axis
    cam.rotation_euler = Euler((pi/2, 0.0, pi/2), 'XYZ') # pointing towards the origin

    # execute the operator
    result = bpy.ops.object.foreach_ex("INVOKE_DEFAULT")
    # this is not a unit test, but at least we know that the operator works
    assert result == {"FINISHED"}

    unregister()

    if (
        profile
        and hasattr(profile, "print_stats")
        and environ.get("LINE_PROFILE") == "1"
    ):
        profile.print_stats()  # type:ignore
