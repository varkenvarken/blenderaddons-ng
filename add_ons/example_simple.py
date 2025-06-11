bl_info = {
    "name": "Simple Move X Operator",
    "author": "Your Name",
    "version": (0, 0, 20250611074806),
    "blender": (4, 4, 0),
    "location": "Object > Move X",
    "description": "Move the active object along the X axis",
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
from bpy.types import Object, Context


class OBJECT_OT_move_x(bpy.types.Operator):
    bl_idname = "object.move_x"
    bl_label = "Move X"
    bl_options = {"REGISTER", "UNDO"}

    amount: bpy.props.FloatProperty(
        name="Amount", description="Amount to move along X axis", default=1.0
    )

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
        obj.location.x += self.amount  # type: ignore (because of the poll() method that ensures obj is not None)

    def execute(self, context: Context) -> set[str]:  # type: ignore
        """Move the active object along the X axis."""
        self.do_execute(context)
        return {"FINISHED"}


OPERATOR_NAME: str = OBJECT_OT_move_x.__name__


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_move_x.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_move_x)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_move_x)


if __name__ == "__main__":  # pragma: no cover
    # this code is for profiling purposes only
    # it is not part of the add-on functionality
    # we simply register the operator, create a cube,
    # and invoke the operator to move the cube along the X axis.
    # if the LINE_PROFILE environment variable is set to "1",
    # the line_profiler will profile the execution of the operator.
    # and print the profiling results.

    register()

    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    obj.location.x = 0.0
    amount = 2.5
    result = bpy.ops.object.move_x("INVOKE_DEFAULT", amount=amount)
    # this is not a unit test, but at least we know that the operator works
    assert result == {"FINISHED"}

    unregister()

    if (
        profile
        and hasattr(profile, "print_stats")
        and environ.get("LINE_PROFILE") == "1"
    ):
        profile.print_stats()  # type:ignore
