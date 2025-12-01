from sys import path
import pytest

pytest.importorskip("bpy")

from math import pi, sin, cos
import numpy as np
import bpy
from mathutils import Matrix


import blempy


@pytest.fixture
def cube():
    # strictly speaking it is not documented in which order the 8 vertices of a primitive cube are laid out in memory, but this will probably never change
    yield np.array(
        [
            [-1.0, -1.0, -1.0],
            [-1.0, -1.0, 1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0],
            [1.0, 1.0, -1.0],
            [1.0, 1.0, 1.0],
        ],
        dtype=np.float32,
    )


@pytest.fixture
def identity3():
    yield Matrix.Identity(3)


@pytest.fixture
def identity4():
    yield Matrix.Identity(4)


class TestPropertyCollection:
    def test_vertex_co_property_get(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        test_proxy.get()

        # the primitive cube has 8 vertices
        assert test_proxy.items == 8
        assert test_proxy.length == 3
        assert test_proxy.ndarray.dtype == np.float32
        assert np.allclose(test_proxy.ndarray, cube)

        # Subdivide the primitive cube
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.subdivide(number_cuts=1)
        bpy.ops.object.mode_set(mode="OBJECT")

        test_proxy.get()

        # the subdivided cube has 26 vertices now, so reallocation should have occured
        assert test_proxy.items == 26
        assert test_proxy.length == 3
        assert test_proxy.ndarray.dtype == np.float32

    def test_vertex_co_property_set(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        test_proxy.get()

        # move every vertex 1 unit in the z direction
        test_proxy.ndarray[:, 2] += 1
        assert np.allclose(test_proxy.ndarray, cube + [0, 0, 1])

        # copy it back
        test_proxy.set()

        # deliberately deallocate the original array and then retrieve the vertex data again
        test_proxy.ndarray = None
        test_proxy.get()

        # it should match the moved coordinates
        assert np.allclose(test_proxy.ndarray, cube + [0, 0, 1])

    def test_vertex_co_property_iterator(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "hide")

        test_proxy.get()

        assert len(test_proxy) == 8  # eight verts in a cube

        for item in test_proxy:
            assert item == False  # noqa: E712

        for item in test_proxy:
            item[:] = True

        assert np.all(test_proxy.ndarray)

        # copy it back
        test_proxy.set()

        # deliberately deallocate the original array and then retrieve the vertex data again
        test_proxy.ndarray = None
        test_proxy.get()

        # it should match the moved coordinates
        assert np.all(test_proxy.ndarray)

    def test_vertex_co_property_matmul_rotate3(self, cube, identity3):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        test_proxy.get()

        # mutliplication by the identity matrix should not change anything
        result = test_proxy @ identity3
        assert (
            result is test_proxy
        )  # multiplication is in place, i.e. left hand side is returned
        assert np.allclose(result.ndarray, cube)

        # rotate all vertice 45 degrees around the z-axis
        rot_z_45deg = Matrix.Rotation(pi / 4, 3, [0, 0, 1])
        result = test_proxy @ rot_z_45deg

        # compare to the list of vertices rotated one by one
        s = sin(pi / 4)
        c = cos(pi / 4)
        cube_rotated = [[v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]] for v in cube]
        np.allclose(result.ndarray, cube_rotated)

    def test_vertex_co_property_extend_discard(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        # the default extends with a 1
        test_proxy.get()
        test_proxy.extend()

        # the original 3 dimensions should be untouched
        assert np.allclose(test_proxy.ndarray[:, :3], cube)
        # and the 4th dimension should be all ones
        assert np.allclose(test_proxy.ndarray[:, 3], 1)

        # we should not be able to set a 4d vector to a 3d property attribute
        with pytest.raises(ValueError):
            test_proxy.set()

        # after discarding the 4th dimension there should be no problem
        test_proxy.discard()
        test_proxy.set()

        # the first 3 dimensions should be unaffected
        assert np.allclose(test_proxy.ndarray, cube)

        # for normals (which should not be affected by the translation part of a 4x4 matrix) we want to extend with zeros
        test_proxy.get()
        test_proxy.extend(normal=True)

        # the first 3 dimensions should still be unaffected
        assert np.allclose(test_proxy.ndarray[:, :3], cube)
        # but the 4th dimension should be all zeros
        assert np.allclose(test_proxy.ndarray[:, 3], 0)

    def test_vertex_co_property_matmul_rotate4(self, cube, identity4):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        test_proxy.get()
        test_proxy.extend()

        # mutliplication by the identity matrix should not change anything
        result = test_proxy @ identity4
        assert (
            result is test_proxy
        )  # multiplication is in place, i.e. left hand side is returned
        assert np.allclose(result.ndarray[:, :3], cube)

        # rotate all vertice 45 degrees around the z-axis
        rot_z_45deg = Matrix.Rotation(pi / 4, 4, [0, 0, 1])
        result = test_proxy @ rot_z_45deg

        # compare to the list of vertices rotated one by one
        s = sin(pi / 4)
        c = cos(pi / 4)
        cube_rotated = [[v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]] for v in cube]
        np.allclose(result.ndarray[:, :3], cube_rotated)

    def test_vertex_co_property_matmul_translate4(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        test_proxy.get()
        test_proxy.extend()

        # translate 1 unit along the z-axis
        rot_z_45deg = Matrix.Translation([0, 0, 1])
        result = test_proxy @ rot_z_45deg

        # check that the matrix multiplication in this case is identical to a direct translation
        np.allclose(result.ndarray[:, :3], cube + [0, 0, 1])

    def test_vertex_co_property_empty_mesh(self):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")
        # not empty, but forgetting to retrieve the actual data will also prevent a discard
        with pytest.raises(ValueError):
            test_proxy.discard()

        # remove all vertices from the primitive cube
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete()
        bpy.ops.object.mode_set(mode="OBJECT")

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        with pytest.raises(ValueError):
            test_proxy.get()

        with pytest.raises(ValueError):
            test_proxy.set()

        with pytest.raises(ValueError):
            test_proxy.extend()

        with pytest.raises(ValueError):
            test_proxy.discard()

    def test_vertex_co_property_extend_no_data(self):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "vertices", "co")

        # extend without get should raise an exception
        with pytest.raises(ValueError):
            test_proxy.extend()

        # the primitive cube has a default uv layer. uv layers are two dimensional, so we do not allow extension, nor discarding
        test_proxy = blempy.PropertyCollection(
            obj.data.uv_layers.active, "uv", "vector"
        )
        test_proxy.get()
        with pytest.raises(ValueError):
            test_proxy.extend()
        with pytest.raises(ValueError):
            test_proxy.discard()

    def test_face_area_property(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "polygons", "area")
        test_proxy.get()

        # the primitive cube has 6 faces
        assert test_proxy.items == 6
        assert (
            test_proxy.length == 1
        )  # area is a scalar, so i n this case dimension should be 1
        assert test_proxy.ndarray.dtype == np.float32
        assert np.allclose(
            test_proxy.ndarray, 4
        )  # default cube has edge lengths of 2, so area = 2 x 2

        assert test_proxy[0] == 4

        test_proxy[0] = 3
        test_proxy.set()

        # set it to None, and get them again to see what we actually wrote to the mesh
        test_proxy.ndarray = None
        test_proxy.get()
        # since area is a read only attribute, everything should have stayed the same (but Blender won´t throw an error)
        assert np.allclose(test_proxy.ndarray, 4)

    def test_face_hide_property(self):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "polygons", "hide")
        test_proxy.get()

        # the primitive cube has 6 faces
        assert test_proxy.items == 6
        assert (
            test_proxy.length == 1
        )  # hide is a scalar, so in this case dimension should be 1
        assert test_proxy.ndarray.dtype == bool
        assert np.allclose(
            test_proxy.ndarray, [False] * 6
        )  # initially they are all visible

        test_proxy[0] = True
        test_proxy.set()
        # set it to None, and get them again to see what we actually wrote to the mesh
        test_proxy.ndarray = None
        test_proxy.get()
        assert np.allclose(test_proxy.ndarray, [True] + [False] * 5)

    def test_edge_hide_property(self):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.PropertyCollection(obj.data, "edges", "hide")
        test_proxy.get()

        # the primitive cube has 12 edges
        assert test_proxy.items == 12
        assert (
            test_proxy.length == 1
        )  # hide is a scalar, so in this case dimension should be 1
        assert test_proxy.ndarray.dtype == bool
        assert np.allclose(
            test_proxy.ndarray, [False] * 12
        )  # initially they are all visible

        test_proxy[0] = True
        test_proxy.set()
        # set it to None, and get them again to see what we actually wrote to the mesh
        test_proxy.ndarray = None
        test_proxy.get()
        assert np.allclose(test_proxy.ndarray, [True] + [False] * 11)


class TestUnifiedAttribute:
    def test_unified_attribute_color(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # the primitive cube does not have a vertex color layer by default
        # so we add it using the old styl vertex_colors (but this will
        # show up in the unified attributes)
        obj.data.vertex_colors.new(name="ACol")

        # first a few negatives
        with pytest.raises(ValueError, match="unknown property"):
            proxy = blempy.UnifiedAttribute(obj.data, "UNKNOWN", "color_srgb")
        with pytest.raises(ValueError, match="does not have an attribute"):
            proxy = blempy.UnifiedAttribute(obj.data, "ACol", "UNKNWON")

        proxy = blempy.UnifiedAttribute(obj.data, "ACol", "color_srgb")

        # cube has six faces
        assert len(proxy) == 6

        # test the iterator by setting all loops in each individual face to a distinct grey level
        # this will cause the face to have a uniform color
        for index, polygon_loops in enumerate(proxy):
            grey_level = index / 6
            polygon_loops[:] = [grey_level, grey_level, grey_level, 1.0]
        proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = proxy.loop_attributes.ndarray
        proxy.loop_attributes.ndarray = None
        proxy.get()

        # this is here to check iwhat the values are if they do not match
        # I still find it baffling that assigned values will be silently converted
        # but that is an issue regardless of this library.
        # for org,col in zip(original, vcol_proxy.loop_attributes.ndarray):
        #     print(f"{org} {col}")
        assert np.allclose(original, proxy.loop_attributes.ndarray, atol=0.01)

    def test_unified_attribute_uvmap(self):
        bpy.ops.mesh.primitive_plane_add()
        obj = bpy.context.active_object

        # the primitive plane has a uv map by default
        # we don´t specify an attribute in the proxy constructor so it should give us the default (i.e. vector)
        proxy = blempy.UnifiedAttribute(obj.data, "UVMap")
        assert proxy.attr == "vector"

        # a plane has a single face
        assert len(proxy) == 1

        proxy.get()

        # get the first (and only) set of uv-coordinates
        uv_coordinates = proxy[0]
        np.allclose(uv_coordinates, [[0, 0], [1, 0], [1, 1], [0, 1]])

        # scale them by a half and write back
        # uv_coordinates is a view, so no need to store it explicitly in the proxy
        uv_coordinates *= 0.5
        proxy.set()

        # force reload from mesh to check if put succeeded
        proxy.loop_attributes.ndarray = None
        proxy.get()

        uv_coordinates = proxy[0]
        np.allclose(uv_coordinates, [[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5]])

        # cannot assign to a non existing face
        with pytest.raises(IndexError):
            proxy[1] = 0

        # but we can to an existing one (numpy will take care of converting the python list)
        proxy[0] = [[0, 0], [1, 0], [1, 1], [0, 1]]

        # force reload from mesh to check if put succeeded
        proxy.loop_attributes.ndarray = None
        proxy.get()

        uv_coordinates = proxy[0]
        np.allclose(uv_coordinates, [[0, 0], [1, 0], [1, 1], [0, 1]])

    def test_unified_attribute_alternates(self):
        bpy.ops.mesh.primitive_plane_add()
        obj = bpy.context.active_object

        # the primitive plane has a uv map by default
        proxy = blempy.UnifiedAttribute(obj.data, "UVMap")
        # but non-existing names raise an error
        with pytest.raises(ValueError):
            proxy = blempy.UnifiedAttribute(obj.data, "Can I haz cheezeburger?")

        # using an index is ok too, but we don´t know the index of the default UVMap so we figure it out first before we use that index to test
        for i, attribute in enumerate(obj.data.attributes):
            if attribute.name == "UVMap":
                proxy = blempy.UnifiedAttribute(obj.data, i)
                break
        # a non existing index is not ok
        with pytest.raises(ValueError):
            proxy = blempy.UnifiedAttribute(obj.data, 120)

        # an Attribute reference should be fine as well
        proxy = blempy.UnifiedAttribute(obj.data, obj.data.attributes["UVMap"])

        # but in that case we are not allowed to pass an attribute name
        with pytest.raises(ValueError):
            proxy = blempy.UnifiedAttribute(
                obj.data, obj.data.attributes["UVMap"], "UVMap"
            )

    def test_unified_attribute_edge_crease(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # quick way to add an edge crease layer to a mesh
        obj.data.edge_creases_ensure()

        # the default name is crease-edge
        proxy = blempy.UnifiedAttribute(obj.data, "crease_edge")

        proxy.get()

        for edge_attribute in proxy:
            edge_attribute[:] = 1.0

        proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = proxy.loop_attributes.ndarray
        proxy.loop_attributes.ndarray = None
        proxy.get()
        assert np.allclose(original, proxy.loop_attributes.ndarray)

    def test_unified_attribute_vertex_crease(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # quick way to add an vertex crease layer to a mesh
        obj.data.vertex_creases_ensure()

        # the default name is crease_vert
        proxy = blempy.UnifiedAttribute(obj.data, "crease_vert")

        proxy.get()

        for vertex_attribute in proxy:
            vertex_attribute[:] = 1.0

        proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = proxy.loop_attributes.ndarray
        proxy.loop_attributes.ndarray = None
        proxy.get()
        assert np.allclose(original, proxy.loop_attributes.ndarray)

    def test_unified_attribute_face(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # there are by default no face attribute layers so create one from scratch
        obj.data.attributes.new(name="oink", type="FLOAT", domain="FACE")

        # the default name is crease_vert
        proxy = blempy.UnifiedAttribute(obj.data, "oink")

        proxy.get()

        for vertex_attribute in proxy:
            vertex_attribute[:] = 1.0

        proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = proxy.loop_attributes.ndarray
        proxy.loop_attributes.ndarray = None
        proxy.get()
        assert np.allclose(original, proxy.loop_attributes.ndarray)

    def test_unified_attribute_vertex_position(self, cube):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        proxy = blempy.UnifiedAttribute(obj.data, "position")

        proxy.get()

        # cube has 8 vertices
        assert len(proxy) == 8

        # we're gonna test 4x4 matrix multiplication so we need to convert the 3D vectors to 4D vectors
        proxy.extend()

        # rotate all vertices 45 degrees around the z-axis
        rot_z_45deg = Matrix.Rotation(pi / 4, 4, [0, 0, 1])
        result = proxy @ rot_z_45deg

        # compare to the list of vertices rotated one by one
        s = sin(pi / 4)
        c = cos(pi / 4)
        cube_rotated = [[v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]] for v in cube]
        np.allclose(result.loop_attributes.ndarray[:, :3], cube_rotated)

        # we should not try to copy that extra 4th column back, so drop it before we call set()
        proxy.discard()
        proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = proxy.loop_attributes.ndarray
        proxy.loop_attributes.ndarray = None
        proxy.get()

        assert np.allclose(original, proxy.loop_attributes.ndarray)

    def test_unified_attribute_vertex_position_pointcloud(self):
        bpy.ops.object.pointcloud_random_add()

        obj = bpy.context.active_object

        proxy = blempy.UnifiedAttribute(obj.data, "position")

        proxy.get()

        # default random point cloud has more than zero points
        assert len(proxy)

        initial_positions = proxy.loop_attributes.ndarray.copy()
        # we're gonna test 4x4 matrix multiplication so we need to convert the 3D vectors to 4D vectors
        proxy.extend()

        # rotate all vertices 45 degrees around the z-axis
        rot_z_45deg = Matrix.Rotation(pi / 4, 4, [0, 0, 1])
        result = proxy @ rot_z_45deg

        # compare to the list of vertices rotated one by one
        s = sin(pi / 4)
        c = cos(pi / 4)
        cube_rotated = [[v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]] for v in initial_positions]
        np.allclose(result.loop_attributes.ndarray[:, :3], cube_rotated)

        # we should not try to copy that extra 4th column back, so drop it before we call set()
        proxy.discard()
        proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = proxy.loop_attributes.ndarray
        proxy.loop_attributes.ndarray = None
        proxy.get()

        assert np.allclose(original, proxy.loop_attributes.ndarray)
