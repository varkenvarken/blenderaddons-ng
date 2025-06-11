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

    def execute(self, context: Context) -> set[str]:  # type: ignore
        """Move the active object along the X axis."""
        obj: Object | None = context.active_object
        obj.location.x += self.amount  # type: ignore (because of the poll() method that ensures obj is not None)
        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_move_x.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_move_x)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_move_x)


if __name__ == "__main__":
    register()
