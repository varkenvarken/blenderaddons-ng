# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from math import cos, pi, sin

import blf
import bpy
import gpu
import numpy as np

from bpy_extras import view3d_utils
from mathutils import Vector
from gpu_extras.batch import batch_for_shader

from .utils import get_package_name

from typing import cast, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from .preferences import PlumbLinePreferences

uniform_shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
smooth_shader_2d = gpu.shader.from_builtin("SMOOTH_COLOR")


def draw_line(
    p0: Sequence[float] | Vector,
    p1: Sequence[float] | Vector,
    color: Sequence,
    width: int,
):
    """
    Draw a line from p0 -> p0 in 3d space with a given color an width.

    :param p0: Vector
    :param p1: Vector
    :param color: Vector (4 elements, rgba)
    :param width: int
    """
    batch = batch_for_shader(
        uniform_shader, "LINES", {"pos": cast(Sequence[Sequence[float]], [p0, p1])}
    )  # again that bloody cast! is a list not a Sequence?
    uniform_shader.bind()
    uniform_shader.uniform_float("color", color)
    uniform_shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])  # type: ignore we are never called outside a valid viewport
    uniform_shader.uniform_float("lineWidth", width)
    batch.draw(uniform_shader)


# some precomputed data for a disk consisting of tris that share a common vertex in the middle
DISK_SEGMENTS = 32

unit_circle = np.array(
    [(0, 0)]
    + [
        (cos(2 * pi * t / DISK_SEGMENTS), sin(2 * pi * t / DISK_SEGMENTS))
        for t in range(DISK_SEGMENTS + 1)
    ],
    dtype=np.float32,
)
indices = [(0, i, i + 1) for i in range(1, DISK_SEGMENTS + 1)]
colors = np.zeros((DISK_SEGMENTS + 2, 4), dtype=np.float32)


def draw_disk(pos, radius, color):
    circle = (unit_circle * radius + np.array((pos.x, pos.y), dtype=np.float32))[
        indices
    ]
    circle.shape = -1, 2
    colors[:, :3] = color[:3]  # ignore alpha
    colors[0, 3] = 1  # center vertex fully opaque
    colors[1:, 3] = 0  # all other vertices at the edge fully transparent
    circle_colors: Sequence[Sequence[float]] = cast(
        Sequence[Sequence[float]], colors[indices].reshape(-1, 4)
    )
    batch = batch_for_shader(
        smooth_shader_2d, "TRIS", {"pos": circle, "color": circle_colors}
    )
    uniform_shader.bind()
    batch.draw(smooth_shader_2d)


def draw_handler_post_view():
    """
    This handler is responsible for drawing the 'plumb line' in the 3d view.

    It deals with view camera settings like perspective and clipping automatically.
    """
    # see why I think tupe checking in Python is such a mess?
    # the asserts are because Blender does not guarantee that those attributes contain something,
    # even though we know they will in our case, but because the actual preferences we retrieve can be None too,
    # and even worse, its type if not None will be AddonPreferences we need to tell the type checker the actual type
    # (PlumbLinePreferences) of our prefs variable, and the cast is needed because otherwise it looks like we are
    # assigning an instance of the superclass. Also, the type annotation needs to be in quotes, because we only
    # import PlumbLinePreferences when typ checking (to prevent accidental circular imports),
    # resulting in this unreadable mess. I am open to discuss PRs that do this more elegantly (i.e. give us both type checking and readability)
    assert bpy.context.preferences is not None
    assert bpy.context.preferences.addons is not None
    assert bpy.context.scene is not None

    prefs: "PlumbLinePreferences" = cast(
        "PlumbLinePreferences",
        bpy.context.preferences.addons[get_package_name()].preferences,
    )

    draw_line(
        bpy.context.scene.cursor.location,
        bpy.context.window_manager.target,  # type: ignore
        prefs.linecolor,
        prefs.linewidth,
    )


def draw_handler_post_pixel():
    assert bpy.context.preferences is not None
    assert bpy.context.preferences.addons is not None
    assert bpy.context.region is not None
    assert bpy.context.space_data is not None
    assert type(bpy.context.space_data) is bpy.types.SpaceView3D
    assert bpy.context.space_data.region_3d is not None

    prefs: "PlumbLinePreferences" = cast(
        "PlumbLinePreferences",
        bpy.context.preferences.addons[get_package_name()].preferences,
    )

    gpu.state.blend_set("ALPHA")

    coords_2d = view3d_utils.location_3d_to_region_2d(
        region=bpy.context.region,
        rv3d=bpy.context.space_data.region_3d,
        coord=bpy.context.window_manager.target,  # type:ignore type checker does not like dynamically assigned attributes
    )
    if coords_2d:
        # if we don´t want to have a fixed radius but one that scales with the zoom
        # we should use location_3d_to_region_2d or something for 2 points facing the camera
        # to determine their 2d locations and take the distance ...
        # or perhaps move this to post_view and draw a sphere instead of a disk ...
        draw_disk(coords_2d, 20, prefs.targetcolor)

        font_id = 0
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 5, 0, 0, 0, 0.7)
        blf.shadow_offset(font_id, 2, -2)
        fontsize = prefs.fontsize
        offset = Vector((0, 30))
        coords_2d += offset
        blf.position(0, *coords_2d, 0)  # type:ignore coords_2d is a Vector of size 2, and unpacking will yield 2 items, but the type checker cannot know that because location_3d_to_region_2d is annotated to return a vector of any size
        blf.size(font_id, fontsize)
        blf.color(font_id, *prefs.fontcolor)

        blf.draw(font_id, bpy.context.window_manager.distance_label) # type:ignore type checker does not like dynamically assigned attributes
