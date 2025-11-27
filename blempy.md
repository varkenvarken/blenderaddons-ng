# blempy — Blender ↔ NumPy helpers

`blempy` provides small, safe utilities to efficiently transfer Blender property-collection attributes (e.g. vertex coordinates) to/from NumPy arrays and perform vectorized operations with minimal Python overhead.

> [!NOTE]  
> This module is not fully fleshed out yet, and its contents/interface may change

## Key classes
- PropertyCollectionAttributeProxy
  - Purpose: bulk transfer for any property-collection attribute (uses foreach_get/foreach_set).
  - Important members:
    - get(): fills/allocates a float32 NumPy array from the property collection.
    - set(): writes the NumPy array back to the property collection.
    - ndarray, items, length: current array and shape metadata.
  - Behavior: automatically reallocates array when collection size or vector length changes. Raises ValueError on empty collections.

- VectorCollectionProxy (subclass)
  - Purpose: conveniences for 3D/4D vector collections.
  - Methods:
    - extend(normal=False): append a 4th column (ones by default, zeros if normal=True).
    - discard(): remove the 4th column.
    - \_\_matmul__(matrix): apply a matrix to all vectors (in-place) and return self.

- LoopVectorAttributeProxy
  - Purpose: conveniences loop layer attributes.
  - Methods:
    - \_\_matmul____(matrix): apply a matrix to all vectors (in-place) and return self.
    - \_\_iter____ and \_\_next____: to return all the loop layer attributes for each polygon in a mesh
    - \_\_len____: returns the number of polygons in a mesh
  
## Characteristics / notes
- Uses dtype float32 for most buffers, and int for indices.
- Designed around Blender's volatile property-collection references — proxies compute references on each get/set.
- Intended for workflows where mesh data is read/written in bulk (faster than per-item Python attribute access).
- Raises clear exceptions for empty collections or incompatible shapes.

## Minimal usage example
```python
from mathutils import Matrix
from bpy.context import active_object
from blempy import VectorCollectionProxy

mesh = active_object.data
vproxy = VectorCollectionProxy(mesh, "vertices", "co")
vproxy.get()                        # load vertex coordinates into vproxy.ndarray
vproxy.extend()                     # convert to 4D so that matrix multiplication
                                    # can deal with translation too
# combine a rotation and a translation into a single matrix
matrix = Matrix.Rotation(pi/4, 4, [0,0,1])
matrix = matrix @ Matrix.Translation(4, [0,0,1])    
vproxy = vproxy @ matrix            # transform in-place
vproxy.discard()                    # discard the 4th column
vproxy.set()                        # write back to mesh
```

## Installation

for now, simply copy the [blempy](/blempy/) folder into your PYTHONPATH. We might convert this to a proper pypi package in the future

## TODO

- [ ] additional convenience functions for frequently used vector operations like translate, scale, rotate, space conversions, ...
- [ ] ... possibly even mapped to dunder methods (like `__add__` for translation or `__mul__` for scale, etc.)
- [x] a specific subclass to deal with properties that are associated with the loop layer, like vertex colors and uv coordinates