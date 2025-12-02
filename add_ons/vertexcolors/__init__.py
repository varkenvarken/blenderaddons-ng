bl_info = {
    "name": "Random vertex colors",
    "author": "Michel Anders (varkenvarken)",
    "version": (0, 0, 20251202130436),
    "blender": (4, 4, 0),
    "location": "Paint > Random vertex color",
    "description": "assign per face random vertex colors",
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
from random import random
import bpy
from bpy.types import Object, Context

from .blempy import UnifiedAttribute


class OBJECT_OT_random_vertex_colors(bpy.types.Operator):
    bl_idname = "object.random_vertex_colors"
    bl_label = "Random vertex colors"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode == "PAINT_VERTEX"

    @profile  # type: ignore (if line_profiler is available)
    def do_execute(self, context: Context) -> None:
        """Expensive part is moved out of the execute method to allow profiling.

        Note that no profiling is done if line_profiler is not available or
        if the environment variable `LINE_PROFILE` is not set to "1".
        """
        obj: Object | None = context.active_object

        # add a new vertex color layer
        obj.data.vertex_colors.new(name="Random")

        # create a proxy for it
        proxy = UnifiedAttribute(obj.data, "Random")

        # assign a random, fully opaque color to all loops in each face
        proxy.get()
        for polygon_loops in proxy:
            # note the [:] here, we want to assign to the ndarray elements,
            # not just rebind the loop variable
            polygon_loops[:] = [random(), random(), random(), 1.0]
        proxy.set()
        
    def execute(self, context: Context) -> set[str]:  # type: ignore
        """Assign random vertex colors to each face"""
        self.do_execute(context)
        return {"FINISHED"}


OPERATOR_NAME: str = OBJECT_OT_random_vertex_colors.__name__


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_random_vertex_colors.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_random_vertex_colors)
    bpy.types.VIEW3D_MT_paint_vertex.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_paint_vertex.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_random_vertex_colors)

