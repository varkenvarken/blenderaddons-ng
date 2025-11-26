from bpy.types import ID
import numpy as np

"""
This module contains several utility classes which allow for efficient manipulation of property collections.

The class
"""

class PropertyCollectionAttributeProxy:
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

        :raises: ValueError if the property collection is empty.
        """
        property_collection = getattr(self.object, self.property_collection)
        items = len(property_collection)
        if items:
            length = len(getattr(property_collection[0], self.atttribute))
            # if we haven't allocated an array yet or its shape has changed, we allocate one
            if self.ndarray is None or items != self.items or length != self.length:
                self.ndarray = np.empty(items * length, dtype=np.float32)
                self.items = items
                self.length = length
            property_collection.foreach_get(self.atttribute, self.ndarray.ravel())
            self.ndarray.shape = self.items, self.length
        else:
            self.items = 0
            self.length = 0
            self.ndarray = None  # type: ignore
            raise ValueError("empty property collection")

    def set(self):
        """
        Transfer the data in the numpy array to the property collection attribute.

        :raises: ValueError if the property collection is empty or its dimensions do not match the numpy array.
        """
        property_collection = getattr(self.object, self.property_collection)
        
        if not len(property_collection):
            raise ValueError("empty property collection")

        length = len(getattr(property_collection[0], self.atttribute))
        if length != self.length:
            raise ValueError("vector length does not match length of property attribute")
        
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
        self.ndarray = np.append(self.ndarray, (np.zeros if normal else np.ones)((self.items,1), dtype=np.float32), axis=1)
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
        self.ndarray = self.ndarray[:,:3]
        self.length = 3

    def __matmul__(self, matrix):
        np.dot(self.ndarray, matrix)
        return self
