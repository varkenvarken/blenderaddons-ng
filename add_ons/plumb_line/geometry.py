# SPDX-FileCopyrightText: © 2016 Michel Anders (varkenvarken) & contributors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import numpy as np
import numpy.typing as npt

from mathutils import Matrix


def max_world_z_of_bounding_box(bb: npt.ArrayLike, world_matrix: Matrix) -> float:
    bb = np.array(bb)
    bb = np.append(  # add 4th dimension == 1 to each vector so the matrix multiplication will perform translation too
        bb,
        np.ones((len(bb), 1), dtype=np.float32),
        axis=1,
    )
    world_bb = np.dot(bb, np.array(world_matrix).T)   # not need to remove the 4th column
    return np.max(world_bb[:, 2])
