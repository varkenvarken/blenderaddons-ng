from bpy.types import ID, Mesh, PointCloud, Attribute, bpy_prop_collection
import numpy as np
from numpy.typing import ArrayLike

"""
This module contains several utility classes which allow for efficient manipulation of property collections.

The class `PropertyCollection` takes care of allocating suitably sized and shaped numpy ndarrays 
when getting attributes from a property collection and can also copy those values back.

The class `UnifiedAttribute` is designed to deal with unified attribute layers, including those in the CORNER domain.
These so called loop layers are associated with, but separated from, faces and indexed using loop indices stored
with a face. These loop indices are property collections too, but this is all dealt with transparently.

Both classes behave like lists: they can be iterated over and allow index based access.

They also provide utility functions to work with properties that are vectors, for example they
have methods to convert between 3D and 4D vectors as well as a __matmul__ method for matrix multiplication with
the `@` operator, which will apply the matrix multiplication to the whole collection of vectro properties at once.
"""

class PropertyCollection:
    def _property_from_key(self):
        """
        Utility function to convert a property name to an actual propert object reference.
        """
        if self.property_collection.isidentifier():
            return getattr(self.object, self.property_collection)
        bracket = self.property_collection.index("[")
        prop = self.property_collection[:bracket]
        name = self.property_collection[bracket + 2 : -2]
        property_collection = getattr(self.object, prop)
        return property_collection[name].data

    def __init__(
        self, obj: ID, property_collection: str, attribute: str
    ) -> None:
        """
        Initialize an property collection proxy.

        This base class provides methods to transfer data to and from a numpy array
        and iterate over items.

        It is smart enough to figure out the necessary shape of the numpy array and
        it will balk when dealing with empty property collections.

        :param obj: any Blender ID object (for example, a bpy.types.Mesh)
        :param property_collection: the name of the property collection (e.g. "vertices").
        :param attribute: the name of the attribute (e.g. "co", for vertex coordinates)

        Note that the property_collection and attribute arguments are passed as strings,
        because before any get or set a new reference to a property collection attribute
        will be calculated because Blender will discard property collections when for
        example the number of vertices in a mesh changes.

        It is ok to create a proxy for an empty collection, but if the collection is still
        empty when any of the methods are called an exception will be raised.
        """
        self.object = obj
        self.property_collection = property_collection
        self.atttribute = attribute
        self.ndarray: np.ndarray = None  # type: ignore
        self.length: int = 0
        self.items: int = 0
        self.extended = False

    def get(self):
        """
        Transfer the property collection attribute data to a numpy array.

        The array will be (re)allocated if necessary.

        :raises: ValueError if the property collection is empty or non-existent
        """
        property_collection = self._property_from_key()

        items = len(property_collection)
        if items:
            attr = getattr(property_collection[0], self.atttribute)
            # check if this attribute is a scalar
            length = len(attr) if hasattr(attr, "__len__") else 1
            attr_type = type(attr) if type(attr) in {bool, int} else np.float32
            # if we haven't allocated an array yet or its shape has changed, we allocate one
            if self.ndarray is None or items != self.items or length != self.length or self.extended:
                self.ndarray = np.empty(items * length, dtype=attr_type)
                self.items = items
                self.length = length
                self.extended = False
            property_collection.foreach_get(self.atttribute, self.ndarray.ravel())
            # we flatten an array if the length of the elements is 1
            # i.e. we never create a 2d array where the last dimension has length 1
            self.ndarray.shape = (
                (self.items, self.length) if self.length > 1 else (self.items,)
            )
        else:
            self.items = 0
            self.length = 0
            self.extended = False
            self.ndarray = None  # type: ignore
            raise ValueError("empty property collection")

    def set(self):
        """
        Transfer the data in the numpy array to the property collection attribute.

        :raises: ValueError if the property collection is empty, non-existent, or its dimensions do not match the numpy array.
        """
        property_collection = self._property_from_key()

        if not len(property_collection):
            raise ValueError("empty property collection")

        attr = getattr(property_collection[0], self.atttribute)
        # check if this attribute is a scalar
        length = len(attr) if hasattr(attr, "__len__") else 1

        if length != self.length:
            raise ValueError(
                f"vector length does not match length of property attribute {self.extended=}"
            )

        property_collection.foreach_set(
            self.atttribute, self.ndarray.ravel()
        )  # ravel() will create a flat view, not a copy, if possible

    def __getitem__(self, key):
        return self.ndarray[key : key + 1]

    def __setitem__(self, key, value):
        self.ndarray[key] = value

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        _index = self._index
        self._index += 1
        if _index >= self.items:
            raise StopIteration
        return self.ndarray[
            _index : _index + 1
        ]  # need to return a reference, not just the value

    def __len__(self):
        return self.items

    # utility methods focused on arrays of vectors

    def extend(self, normal=False):
        """
        Add a 4th column to a collection of 3D vectors.

        :param normal: if True, initialize the 4th column to all zeros. (the default is for all ones)

        :raises: ValueError if the collections is empty, or there are no 3D vectors.
        """
        property_collection = self._property_from_key()
        # property_collection = getattr(self.object, self.property_collection)
        if not len(property_collection):
            raise ValueError("empty property collection")
        if self.ndarray is None:
            raise ValueError("no array allocated. Did you forget to call get() first?")
        if self.ndarray.shape[-1] != 3:
            raise ValueError("can only add a 4th column to an array of 3vectors")
        self.ndarray = np.append(
            self.ndarray,
            (np.zeros if normal else np.ones)((self.items, 1), dtype=np.float32),
            axis=1,
        )
        self.length = 4

    def discard(self):
        """
        Discard the 4th column from a collection of 4D vectors.

        :raises: ValueError if the collections is empty, or there are no 4D vectors.
        """
        property_collection = self._property_from_key()
        # property_collection = getattr(self.object, self.property_collection)
        if not len(property_collection):
            raise ValueError("empty property collection")
        if self.ndarray is None:
            raise ValueError("no array allocated. Did you forget to call get() first?")
        if self.ndarray.shape[-1] != 4:
            raise ValueError("can only discard the 4th column")
        self.ndarray = self.ndarray[:, :3]
        self.length = 3

    def __matmul__(self, matrix:ArrayLike):
        np.dot(self.ndarray, matrix)
        return self


class UnifiedAttribute:
    default_attribute = {
        "BYTE_COLOR": "color",
        "FLOAT_COLOR": "color",
        "FLOAT": "value",
        "INT": "value",
        "BOOLEAN": "value",
        "FLOAT_VECTOR": "vector",
        "QUATERNION": "vector",
        "FLOAT4X4": "value",
        "STRING": "value",
        "INT8": "value",
        "INT16_2D": "vector",
        "INT32_2D": "vector",
        "FLOAT2": "vector",
    }

    def __init__(
        self, mesh: Mesh | PointCloud, name: str | int | Attribute, attr: str | None = None
    ) -> None:
        """
        Initialize an attribute proxy for a unified attribute layer.

        Currently supports loop layer (a.k.a. face corner), face, edge and point attributes only (curve, instance and layer are not supported).

        :param mesh: a bpy.types.Mesh | bpy.types.PointCloud
        :param name: the given name of the property collection (e.g. "Col" or "UVMap"), an index into `attributes`, or a reference to an attribute layer
        :param attribute: the name of the attribute (e.g. "color", for vertex colors)

        If the attr is None, a default is selected (color for vertex color layers, vector or value for others).
        """

        if isinstance(name, str):
            if name not in mesh.attributes.keys():
                raise ValueError(f"unknown property collection {name}")
            collection: Attribute = mesh.attributes[name]
        elif isinstance(name, int):
            try:
                collection: Attribute = mesh.attributes[name]
            except IndexError:
                raise ValueError(f"unknown property index {name}")
            name = collection.name
        elif isinstance(name, Attribute):
            collection = name
            if attr is not None:
                raise ValueError(
                    "attr argument must be None when name argument is a Attribute instance"
                )
            name = collection.name
        else:  # pragma: nocover
            raise TypeError("name argument must be a str, int, or Attribute instance")

        self.data_type = collection.data_type
        self.storage_type = (
            collection.storage_type if hasattr(collection, "storage_type") else "ARRAY"
        )  # versions prior to Blender 5.0 don´t have this attribute
        self.domain = collection.domain

        if attr is None:
            attr = self.default_attribute.get(self.data_type, "value")

        if not hasattr(collection.data[0], attr):
            raise ValueError(f"property {name} does not have an attribute {attr}")

        if self.domain not in {"CORNER", "FACE", "EDGE", "POINT"}:
            raise NotImplementedError(
                f"cannot create a proxy yet for attributes in domain {self.domain}"
            )

        if self.storage_type not in {"ARRAY"}:
            raise NotImplementedError(
                f"cannot create a proxy yet for attributes with storage type {self.storage_type}"
            )

        self.name = name
        self.attr = attr

        match self.domain:
            case "CORNER":
                self.loop_start = PropertyCollection(mesh, "polygons", "loop_start")
                self.loop_start.get()
                self.loop_total = PropertyCollection(mesh, "polygons", "loop_total")
                self.loop_total.get()

                self.loop_attributes = PropertyCollection(
                    mesh, f"attributes['{name}']", attr
                )
                self.loop_attributes.get()
            case "FACE" | "EDGE" | "POINT":
                self.loop_attributes = PropertyCollection(
                    mesh, f"attributes['{name}']", attr
                )
                self.loop_attributes.get()
            case _:
                self.loop_start = None
                self.loop_total = None
                self.loop_attributes = None

    def get(self):
        if self.domain == "CORNER":
            self.loop_start.get()
            self.loop_total.get()
        self.loop_attributes.get()

    def set(self):
        self.loop_attributes.set()

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        polygon = self._index
        self._index += 1
        if self.domain == "CORNER":
            if polygon >= self.loop_start.items:
                raise StopIteration
            start = self.loop_start.ndarray[polygon]
            end = start + self.loop_total.ndarray[polygon]
            return self.loop_attributes.ndarray[start:end]
        else:
            if polygon >= self.loop_attributes.items:
                raise StopIteration
            return self.loop_attributes.ndarray[
                polygon : polygon + 1
            ]  # need to return a reference, not just the value

    def __len__(self):
        if self.domain == "CORNER":
            return self.loop_start.items
        return self.loop_attributes.items

    def __getitem__(self, key):
        if self.domain == "CORNER":
            start = self.loop_start.ndarray[key]
            end = start + self.loop_total.ndarray[key]
            return self.loop_attributes.ndarray[start:end]
        else:
            return self.loop_attributes.ndarray[key]

    def __setitem__(self, key, value):
        if self.domain == "CORNER":
            start = self.loop_start.ndarray[key]
            end = start + self.loop_total.ndarray[key]
            self.loop_attributes.ndarray[start:end] = value
        else:
            self.loop_attributes.ndarray[key] = value

    # utility methods focused on arrays of vectors
    # they forward to the underlying loop_attributes

    def extend(self, normal=False):
        """
        Add a 4th column to a collection of 3D vectors.

        :param normal: if True, initialize the 4th column to all zeros. (the default is for all ones)

        :raises: ValueError if the collections is empty, or there are no 3D vectors.
        """
        self.loop_attributes.extend(normal)

    def discard(self):
        """
        Discard the 4th column from a collection of 4D vectors.

        :raises: ValueError if the collections is empty, or there are no 4D vectors.
        """
        self.loop_attributes.discard()

    def __matmul__(self, matrix):
        self.loop_attributes.__matmul__(matrix)
        return self
