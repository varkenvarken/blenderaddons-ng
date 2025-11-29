![PyPI - Version](https://img.shields.io/pypi/v/blempy)

# blempy — Blender ↔ NumPy helpers

`blempy` provides small, safe utilities to efficiently transfer Blender property-collection attributes (e.g. vertex coordinates) to/from NumPy arrays and perform vectorized operations with minimal Python overhead.

> [!NOTE]  
> This module is not fully fleshed out yet, and its contents/interface may change

## Key classes
- `PropertyCollectionAttributeProxy`
  - Purpose: bulk transfer for any property-collection attribute (uses foreach_get/foreach_set).
  - Important members:
    - get(): fills/allocates a float32 NumPy array from the property collection.
    - set(): writes the NumPy array back to the property collection.
    - ndarray, items, length: current array and shape metadata.
  - Behavior: automatically reallocates array when collection size or vector length changes. Raises ValueError on empty collections.

- `VectorCollectionProxy(PropertyCollectionAttributeProxy)`
  - Purpose: convenient access to 3D/4D vector collections.
  - Methods:
    - extend(normal=False): append a 4th column (ones by default, zeros if normal=True).
    - discard(): remove the 4th column.
    - \_\_matmul__(matrix): apply a matrix to all vectors (in-place) and return self.

- `LoopVectorAttributeProxy`
  - Purpose: convenient access to loop layer attributes, i.e. attributes associated with face corners, like uv-coordinates.
  - Methods:
    - \_\_matmul____(matrix): apply a matrix to all vectors (in-place) and return self.
    - \_\_iter____ and \_\_next____: to return all the loop layer attributes for each polygon in a mesh
    - \_\_len____: returns the number of polygons in a mesh

- `AttributeProxy`
  - Purpose: access to any layer in the unified attribute layers of a Mesh. 
  - Methods:
    - \_\_iter____ and \_\_next____: to return all the loop layer attributes for each polygon in a mesh
    - \_\_len____: returns the number of polygons in a mesh
    - \_\_getitem()\_\_: return a single item (i.e. a vector, a scalar value, or (for lop layer properties) an array of vectors)  
    - \_\_setitem()\_\_: set the value of an item

## Characteristics / notes

- Designed around Blender's volatile property-collection references — proxies compute references on each get/set.
- Intended for workflows where mesh data is read/written in bulk (faster than per-item Python attribute access).
- Raises clear exceptions for empty collections or incompatible shapes.

## Minimal usage examples

Transforming all vertex coordinates:

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

Give all faces of a mesh a uniform but unique random greyscale color:

```python
from random import random
from bpy.context import active_object
from blempy import AttributeProxy

mesh = active_object.data
# assume the mesh already has a vertex color layer called "Color"
proxy = blempy.AttributeProxy(mesh, "Color")

# iterate over faces and set all loops in each individual face to a distinct grey level
# setting all loops to the same value will cause the face to have a uniform color
# NOTE: no need for a proxy.get() call, we will replace all data so we don´t need the originals
for index, polygon_loops in enumerate(proxy):
    grey_level = random()
    polygon_loops[:] = [grey_level, grey_level, grey_level, 1.0]

# sync data back to the mesh
proxy.set()
```

## Installation

`blempy` is available as a package on [pypi](https://pypi.org/project/blempy/) and can be installed in the usual way:

```bash
python -m pip install blempy
```

But that would install the package in the default location. That is fine if you use Blender as a module, but if your are developing for the "complete" Blender, you would need to install it inside your Blender environment. A refresher on how to do that can be found in [this old article](https://blog.michelanders.nl/2021/06/installing-python-packages-with-pip-in-your-blender-environment.html).

If you are developing an addon that uses the `blempy` package, it is probably easiest to bundle it with your add-on, i.e. simply copy the [blempy folder](/blempy/) from the repository into your own project. By copying, you automatically fix the version, so that if blempy gets a breaking update you won´t have to deal with that immediately.

## TODO

- [ ] additional convenience functions for frequently used vector operations like translate, scale, rotate, space conversions, ...
- [ ] ... possibly even mapped to dunder methods (like `__add__` for translation or `__mul__` for scale, etc.)
- [x] a specific subclass to deal with properties that are associated with the loop layer

  like vertex colors and uv coordinates

- [x] extend AttributeProxy to instantiate a proxy by refering to layers directly or by index

  for example to refer mesh.attributes.active directly

- [ ] extend AttributeProxy to work with non-loop attributes
      
  vertex, edge, face, ...

- [ ] extend AttributeProxy to work with BMesh objects
- [ ] extend AttributeProxy to work with non mesh objects

  curve etc.

