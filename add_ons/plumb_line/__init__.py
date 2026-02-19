# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Context, Event
from mathutils import Vector

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # see: https://b3d.interplanety.org/en/how-to-properly-specify-the-return-type-of-the-blender-operator-execute-function/
    from bpy.stub_internal.rna_enums import OperatorReturnItems

from .utils import reload

# force reload from any previously loaded modules in this package (good when developing, saves us from restarting blender to make sure changed modules have effect)
# because we needed to import reload from utils, the utils module itself is always reloaded,
# but any other module is only reloaded if we do a reinstall, it will be loaded just once
# on the first install  or when blender starts up
reload(__name__)

from .handlers import draw_handler_post_view, draw_handler_post_pixel  # noqa: E402 we absolutely need to execute the reload before importing these
from .preferences import PlumbLinePreferences  # noqa: E402 we absolutely need to execute the reload before importing these
from .geometry import max_world_z_of_bounding_box # noqa: E402 we absolutely need to execute the reload before importing these

bl_info = {
    "name": "Plumb line",
    "author": "Michel Anders (varkenvarken)",
    "version": (0, 0, 20260219095531),
    "blender": (5, 0, 0),
    "location": "Object > Plumb line",
    "description": "interactively measure vertical distance",
    "warning": "",
    "doc_url": "https://github.com/varkenvarken/blenderaddons-ng/blob/main/add_ons/plumb_line/readme.md",
    "tracker_url": "https://github.com/varkenvarken/blenderaddons-ng/issues",
    "category": "Object",
}

HELPTEXT = "ESC/Rightmouse exits, Arrow keys / Page Up/Down to move origin (Shift = slow / Ctrl = fast)   S-key to toggle scene intersection"


class OBJECT_OT_plumb_line(bpy.types.Operator):
    bl_idname = "object.plumbline"
    bl_label = "Plumb line"
    bl_options = {"REGISTER"}  # no UNDO needed: this operator doesn´t change anything

    @classmethod
    def poll(cls, context: Context) -> bool:
        return (
            context.mode == "OBJECT" and context.active_object is not None
        )  # Enhancement option: check if object type can be intersected at all (Lights can't for example)

    def modal(self, context: Context, event: Event) -> set["OperatorReturnItems"]:
        """
        Modal handler, gets called on every event.

        Does all the hard work in changing the 3d cursor position on key presses and
        (re)calculating the intersection point using ray casting.
        """
        # these asserts are to keep the type checker happy; we know these attributes are not None
        assert context.area is not None
        assert context.window is not None
        assert context.scene is not None
        assert context.active_object is not None

        context.area.tag_redraw()

        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.cancel(context)
            return {"CANCELLED"}

        if (
            event.type == "S"
        ):  # we only act on release, but catch and ignore the initial press also otherwise we initiate a scale action
            if event.value == "RELEASE":
                print("toggle scene inclusion")
                self.include_scene = not self.include_scene
        elif event.type in {
            "UP_ARROW",
            "DOWN_ARROW",
            "LEFT_ARROW",
            "RIGHT_ARROW",
            "PAGE_UP",
            "PAGE_DOWN",
        }:
            if (
                event.value == "PRESS"
            ):  # not release because we do want to act on press-and-hold
                increment = 0.01
                if event.shift:
                    increment = 0.001
                elif event.ctrl:
                    increment = 0.1
                match event.type:
                    case "UP_ARROW":
                        context.scene.cursor.location.y += increment
                    case "DOWN_ARROW":
                        context.scene.cursor.location.y -= increment
                    case "LEFT_ARROW":
                        context.scene.cursor.location.x -= increment
                    case "RIGHT_ARROW":
                        context.scene.cursor.location.x += increment
                    case "PAGE_UP":
                        context.scene.cursor.location.z += increment
                    case "PAGE_DOWN":
                        context.scene.cursor.location.z -= increment

        # the ray casting onto a scene and onto an object methods don't have the same signature!
        # The position of the depsgraph parameter is different, and the number of values returned is different.
        # Also, ray casting onto a scene is all done in world space, while ray casting onto an object
        # is done in object space
        if self.include_scene:
            # result is True if we have a hit, in which case we get a location in world space
            result, worldspace_location, normal, index, object, matrix = (
                context.scene.ray_cast(
                    self.depsgraph, context.scene.cursor.location, (0, 0, -1)
                )
            )
        else:
            # get the inverted world matrix, so we can map from world space -> object space
            object_space = context.active_object.matrix_world.inverted()
            # get the cursor location and map it to object space
            # note that multiplying this 4x4 matric with a 3-vector implicitely treats this vector as a location vector (i.e. extended with a 1, so translations work too)
            origin = object_space @ context.scene.cursor.location
            # direction vectors shouldn´t be translated, so we add a zero and covert it back to a 3-vector ourselves)
            direction = (object_space @ Vector((0, 0, -1, 0))).to_3d()
            # result is True if we have a hit, in which case location is the spot in object space
            result, location, normal, index = context.active_object.ray_cast(
                origin, direction, depsgraph=self.depsgraph
            )
            # we convert to world space
            worldspace_location = context.active_object.matrix_world @ location

        if result:
            context.window_manager.target = worldspace_location  # type: ignore Type checker is not happy with dynamically assigned attributes.
            context.window_manager.distance_label = f"{(Vector(context.window_manager.target) - context.scene.cursor.location).length:.4f}"  # type: ignore Type checker is not happy with dynamically assigned attributes.
        else:  # no hit
            context.window_manager.target = (  # type: ignore Type checker is not happy with dynamically assigned attributes.
                context.scene.cursor.location
            )
            context.window_manager.distance_label = "----"  # type: ignore Type checker is not happy with dynamically assigned attributes.
        if (
            event.type.find("MOUSE") >= 0 or event.type.find("NUMPAD") >= 0
        ):  # contains "MOUSE" or "NUMPAD" in the type name; allows changing the view
            return {"PASS_THROUGH"}

        # print(f"ignored {event.type=}")  # for debugging purposes, if you want to see which events are ignored completely

        return {"RUNNING_MODAL"}

    def invoke(self, context: Context, event: Event) -> set["OperatorReturnItems"]:
        """
        Called when the operator is selected in a menu.

        Initializes the start environment and adds the operator's modal() method as a modal event handler.
        It also installs the graphical overlay handlers.
        """
        # these asserts are to keep the type checker happy; we know these attributes are not None
        assert context.window is not None
        assert context.window_manager is not None
        assert context.workspace is not None
        assert context.active_object is not None
        assert context.scene is not None

        # we move the cursor to a position above the currently active object
        self.include_scene = True
        # start_location = context.active_object.location.copy()  # type: ignore (cannot be None, that is guarded by poll())
        # start_location.z += (
        #     3  #  TODO: we will adapt that later to just above the bounding box
        # )
        z = max_world_z_of_bounding_box(context.active_object.bound_box, context.active_object.matrix_world)
        context.scene.cursor.location = context.active_object.location.copy()
        context.scene.cursor.location.z = z + 3  # arbitrary offset

        self.depsgraph = (
            context.evaluated_depsgraph_get()
        )  # only get this once for the duration of the modal run

        # eye candy: we change the cursor to give visual feedback that something is happening
        context.window.cursor_modal_set("CROSSHAIR")
        context.window_manager.modal_handler_add(self)

        # context.area.header_text_set("oink")  # don´t use this, as it would display at the top of the 3d view
        context.workspace.status_text_set(
            HELPTEXT
        )  # this will show at the bottom of the window

        # install the handlers responsible for drawing the overlays
        self.post_view_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_handler_post_view, (), "WINDOW", "POST_VIEW"
        )
        self.post_pixel_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_handler_post_pixel, (), "WINDOW", "POST_PIXEL"
        )
        return {"RUNNING_MODAL"}

    def cancel(self, context: Context) -> None:
        """
        Cleanup.

        Removes draw handlers and resets cursor shape to default.
        Does not remove the modal event handler because that is done by Blender itseld when the operator is canceled or finished.
        """
        # these asserts are to keep the type checker happy; we know these attributes are not None
        assert context.area is not None
        assert context.window is not None
        assert context.workspace is not None

        bpy.types.SpaceView3D.draw_handler_remove(self.post_view_handler, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(self.post_pixel_handler, "WINDOW")

        context.window.cursor_modal_restore()
        # context.area.header_text_set(None)
        context.workspace.status_text_set(None)
        context.area.tag_redraw()


def menu_func(self, context):
    self.layout.operator(
        OBJECT_OT_plumb_line.bl_idname,
        text=OBJECT_OT_plumb_line.bl_label,
        icon="PLUGIN",
    )


# for testing purposes, Blender does not require this.
OPERATOR_NAME: str = OBJECT_OT_plumb_line.__name__


def register():
    bpy.utils.register_class(OBJECT_OT_plumb_line)
    bpy.utils.register_class(PlumbLinePreferences)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.WindowManager.target = bpy.props.FloatVectorProperty(name="Target")  # type: ignore Type checker is not happy with dynmically assigned attributes.
    bpy.types.WindowManager.distance_label = bpy.props.StringProperty(name="Distance")  # type: ignore Type checker is not happy with dynmically assigned attributes.


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_plumb_line)
    bpy.utils.unregister_class(PlumbLinePreferences)

    # if the add-on is uninstalled while the modal operator is running
    # the operator's cancel() method apparently isn´t called, so we have to make
    # sure no stray draw handlers get left around
    try:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handler_post_view, "WINDOW")
    except Exception:
        pass
    try:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handler_post_pixel, "WINDOW")
    except Exception:
        pass
