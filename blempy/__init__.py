from bpy.types import ID, Mesh, Attribute
import numpy as np

"""
This module contains several utility classes which allow for efficient manipulation of property collections.

The base class `PropertyCollectionAttributeProxy` takes care of allocating suitably sized and shaped numpy ndarrays 
when getting attributes from a property collection and can also copy those values back.

The class `VectorCollectionProxy` is designed to deal with attributes that are vectors (like vertex coordinates) and
provides method to convert between 3D and 4D vectors as well as a __matmul__ method for matrix multiplication with
the `@` operator.

The `LoopVectorAttributeProxy` is not a subclass but is composed of several `PropertyCollectionAttributeProxy`
instances to provide easy access to attributes associated with loops (i.e. face corners), like uv coordinates and
vertex colors.
"""


class PropertyCollectionAttributeProxy:
    def property_from_key(self):
        if self.property_collection.isidentifier():
            return getattr(self.object, self.property_collection)
        bracket = self.property_collection.index("[")
        prop = self.property_collection[:bracket]
        name = self.property_collection[bracket + 2 : -2]
        property_collection = getattr(self.object, prop)
        return property_collection[name].data

    def __init__(self, obj: ID, property_collection: str, attribute: str) -> None:
        """
        Initialize an attribute proxy.

        This base class only provides methods to transfer data to and from a numpy array.
        It is smart enough to figure out the necessary shape of the numpy array and
        it will balk when dealing with empty property collections.

        :param obj: any Blender ID object (for example, a bpy.types.Mesh)
        :param property_collection: the name of the property collection (e.g. "vertices")
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

    def get(self):
        """
        Transfer the property collection attribute data to a numpy array.

        The array will be (re)allocated if necessary.

        :raises: ValueError if the property collection is empty or non-existent
        """
        property_collection = self.property_from_key()

        items = len(property_collection)
        if items:
            attr = getattr(property_collection[0], self.atttribute)
            # check if this attribute is a scalar
            length = len(attr) if hasattr(attr, "__len__") else 1
            attr_type = int if type(attr) is int else np.float32
            # if we haven't allocated an array yet or its shape has changed, we allocate one
            if self.ndarray is None or items != self.items or length != self.length:
                self.ndarray = np.empty(items * length, dtype=attr_type)
                self.items = items
                self.length = length
            property_collection.foreach_get(self.atttribute, self.ndarray.ravel())
            # we flatten an rray if the length of the elements is 1
            self.ndarray.shape = (
                (self.items, self.length) if self.length > 1 else (self.items,)
            )
        else:
            self.items = 0
            self.length = 0
            self.ndarray = None  # type: ignore
            raise ValueError("empty property collection")

    def set(self):
        """
        Transfer the data in the numpy array to the property collection attribute.

        :raises: ValueError if the property collection is empty, non-existent, or its dimensions do not match the numpy array.
        """
        property_collection = self.property_from_key()

        if not len(property_collection):
            raise ValueError("empty property collection")

        attr = getattr(property_collection[0], self.atttribute)
        # check if this attribute is a scalar
        length = len(attr) if hasattr(attr, "__len__") else 1

        if length != self.length:
            raise ValueError(
                "vector length does not match length of property attribute"
            )

        property_collection.foreach_set(
            self.atttribute, self.ndarray.ravel()
        )  # ravel() will create a flat view, not a copy, if possible


class VectorCollectionProxy(PropertyCollectionAttributeProxy):
    def __init__(self, obj: ID, property_collection: str, attribute: str) -> None:
        """
        Initialize a vector attribute proxy.

        It is designed to work with collections of 3D or 4D vectors and offers
        methods to extend from 3d -> 4D and discard the 4th column from a 4D vector.

        It also provides some convenience methods, specifically __matmul__() which
        allows us to perform matrix multiplications with all vectors in the collection
        in one go, using the @ operator.

        :param obj: any Blender ID object (for example, a bpy.types.Mesh)
        :param property_collection: the name of the property collection (e.g. "vertices")
        :param attribute: the name of the attribute (e.g. "co", for vertex coordinates)

        Note that the property_collection and attribute arguments are passed as strings,
        because before any get or set a new reference to a property collection attribute
        will be calculated because Blender will discard property collections when for
        example the number of vertices in a mesh changes.

        It is ok to create a proxy for an empty collection, but if the collection is still
        empty when any of the methods are called an exception will be raised.
        """
        super().__init__(obj, property_collection, attribute)
        # we would love to add some additional checks here to see if the attribute is indeed
        # a vector, but unfortunately Blender does not have methods to figure this out.
        # so the redefinition of the __init__() method is superfluous, but it doesn´t hurt,
        # and it gives us a opportunity to add a more specific docstring.

    def extend(self, normal=False):
        """
        Add a 4th column to a collection of 3D vectors.

        :param normal: if True, initialize the 4th column to all zeros. (the default is for all ones)

        :raises: ValueError if the collections is empty, or there are no 3D vectors.
        """
        property_collection = getattr(self.object, self.property_collection)
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
        property_collection = getattr(self.object, self.property_collection)
        if not len(property_collection):
            raise ValueError("empty property collection")
        if self.ndarray is None:
            raise ValueError("no array allocated. Did you forget to call get() first?")
        if self.ndarray.shape[-1] != 4:
            raise ValueError("can only discard the 4th column")
        self.ndarray = self.ndarray[:, :3]
        self.length = 3

    def __matmul__(self, matrix):
        np.dot(self.ndarray, matrix)
        return self


def getattrs(obj, attrs: str):
    individual_attributes = attrs.split(".")
    for attr in individual_attributes[:-1]:  # all but the last one
        obj = getattr(obj, attr)
    return obj, individual_attributes[-1]


class LoopVectorAttributeProxy:
    def __init__(self, mesh: Mesh, loop_layer, property_collection: str) -> None:
        """
        Initialize an attribute proxy for attributes associated with a loop layer.

        Loop layer attributes like uv coordinates or vertex colors are always associated
        with the loops (face corners) of mesh polygons (faces) and each polygon has attributes that
        point to the start and end indices of the loops associated with that face.

        This class takes care of retrieving those indices as well as the loop layer attributes
        themselves.

        It also provides some convenience methods, specifically __matmul__() which
        allows us to perform matrix multiplications with all vectors in the collection
        in one go, using the @ operator, and you can iterate over the proxy, yielding
        an array (view) with all the attribute for all the loops in a single polygon

        >>> # set a unique, uniform grey value for each face
        >>> proxy = LoopVectorAttributeProxy(mesh, "vertex_colors.active.data", "color")
        >>> proxy.get()
        >>> for loops in proxy:
        >>>     grey = random()
        >>>     loops[:] = [grey, grey, grey, 1.0]
        >>> proxy.set()

        :param mesh: a bpy.types.Mesh
        :param property_collection: the name of the property collection (e.g. "vertex_colors.active.data" or "vertex_colors['Col']")
        :param attribute: the name of the attribute (e.g. "color", for vertex colors)

        Note that the property_collection and attribute arguments are passed as strings,
        because before any get or set a new reference to a property collection attribute
        will be calculated because Blender will discard property collections when for
        example the number of vertices in a mesh changes.

        It is ok to create a proxy for an empty collection, but if the collection is still
        empty when any of the methods are called an exception will be raised.
        """
        self.loop_start = PropertyCollectionAttributeProxy(
            mesh, "polygons", "loop_start"
        )
        self.loop_start.get()
        self.loop_total = PropertyCollectionAttributeProxy(
            mesh, "polygons", "loop_total"
        )
        self.loop_total.get()

        self.loop_attributes = VectorCollectionProxy(
            *getattrs(mesh, loop_layer), property_collection
        )
        self.loop_attributes.get()

    def get(self):
        self.loop_start.get()
        self.loop_total.get()
        self.loop_attributes.get()

    def set(self):
        self.loop_attributes.set()

    def __iter__(self):
        self.polygon = 0
        return self

    def __next__(self):
        polygon = self.polygon
        self.polygon += 1
        if polygon >= self.loop_start.items:
            raise StopIteration
        start = self.loop_start.ndarray[polygon]
        end = start + self.loop_total.ndarray[polygon]
        return self.loop_attributes.ndarray[start:end]

    def __len__(self):
        return self.loop_start.items


class AttributeProxy:
    default_attribute = {"BYTE_COLOR": "color", "FLOAT_COLOR": "color"}

    def __init__(self, mesh: Mesh, name: str, attr: str | None = None) -> None:
        """
        Initialize an attribute proxy for a unified attribute layer.

        Currently supports loop layer (a.k.a. face corner) attributes only.

        :param mesh: a bpy.types.Mesh
        :param name: the given name of the property collection (e.g. "Col" or "UVMap")
        :param attribute: the name of the attribute (e.g. "color", for vertex colors)

        if the attr is None, a default is selected (color for vertex color layers, vector for others)
        """
        if name not in mesh.attributes.keys():
            raise ValueError(f"unknown property collection {name}")

        collection: Attribute = mesh.attributes[name]
        self.data_type = collection.data_type
        self.storage_type = (
            collection.storage_type if hasattr(collection, "storage_type") else "ARRAY"
        )  # versions prior to Blender 5.0 don´t have this attribute
        self.domain = collection.domain

        if attr is None:
            attr = self.default_attribute.get(self.data_type, "vector")
                
        if not hasattr(collection.data[0], attr):
            raise ValueError(f"property {name} does not have an attribute {attr}")

        if self.domain not in {"CORNER"}:
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
                self.loop_start = PropertyCollectionAttributeProxy(
                    mesh, "polygons", "loop_start"
                )
                self.loop_start.get()
                self.loop_total = PropertyCollectionAttributeProxy(
                    mesh, "polygons", "loop_total"
                )
                self.loop_total.get()
                self.loop_attributes = VectorCollectionProxy(
                    *getattrs(mesh, f"attributes['{name}']"), attr
                )
                self.loop_attributes.get()
            case _:
                self.loop_start = None
                self.loop_total = None
                self.loop_attributes = None

    def get(self):
        self.loop_start.get()
        self.loop_total.get()
        self.loop_attributes.get()

    def set(self):
        self.loop_attributes.set()

    def __iter__(self):
        self.polygon = 0
        return self

    def __next__(self):
        polygon = self.polygon
        self.polygon += 1
        if polygon >= self.loop_start.items:
            raise StopIteration
        start = self.loop_start.ndarray[polygon]
        end = start + self.loop_total.ndarray[polygon]
        return self.loop_attributes.ndarray[start:end]

    def __len__(self):
        return self.loop_start.items

    def __getitem__(self, key):
        start = self.loop_start.ndarray[key]
        end = start + self.loop_total.ndarray[key]
        return self.loop_attributes.ndarray[start:end]

    def __setitem__(self, key, value):
        start = self.loop_start.ndarray[key]
        end = start + self.loop_total.ndarray[key]
        self.loop_attributes.ndarray[start:end] = value
