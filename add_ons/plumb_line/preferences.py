# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from .utils import get_package_name


class PlumbLinePreferences(bpy.types.AddonPreferences):
    bl_idname = get_package_name()  # important: this links these preferences with the current add-on; you still need to register the class though

    linecolor: bpy.props.FloatVectorProperty(
        name="Line color",
        description="Color of the plumb line",
        size=4,
        default=(1, 0, 0, 1),  # red
        subtype="COLOR",
    )

    linewidth: bpy.props.IntProperty(
        name="Line width",
        description="Linewidth of arrows",
        default=1,
        min=1,
        soft_max=5,
    )

    fontsize: bpy.props.IntProperty(
        name="Font size",
        description="Fontsize for labels",
        default=14,
        min=2,
        soft_max=150,
    )

    fontcolor: bpy.props.FloatVectorProperty(
        name="Label color",
        description="Color of the distance label",
        size=4,
        default=(1, 1, 1, 1),  # white
        subtype="COLOR",
    )

    targetcolor: bpy.props.FloatVectorProperty(
        name="Target color",
        description="Color of the highlighted intersection point",
        size=4,
        default=(0, 0, 1, 1),  # blue
        subtype="COLOR",
    )


    # preferences *must* have a draw, there is no default, unlike with operators
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "linecolor")
        row.prop(self, "linewidth")
        row = layout.row()
        row.prop(self, "targetcolor")
        row.label(text=" ")  # just a placeholder to force left alignment
        row = layout.row()
        row.prop(self, "fontcolor")
        row.prop(self, "fontsize")
        
