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


class TestExampleSimple:
    def test_vertex_co_property_get(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

    def test_vertex_co_property_matmul_rotate3(self, cube, identity3):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")
        # not empty, but forgetting to retrieve the actual data will also prevent a discard
        with pytest.raises(ValueError):
            test_proxy.discard()

        # remove all vertices from the primitive cube
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete()
        bpy.ops.object.mode_set(mode="OBJECT")

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

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

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

        # extend without get should raise an exception
        with pytest.raises(ValueError):
            test_proxy.extend()

        # the primitive cube has a default uv layer. uv layers are two dimensional, so we do not allow extension, nor discarding
        test_proxy = blempy.VectorCollectionProxy(
            obj.data.uv_layers.active, "uv", "vector"
        )
        test_proxy.get()
        with pytest.raises(ValueError):
            test_proxy.extend()
        with pytest.raises(ValueError):
            test_proxy.discard()

    def test_uv_layer_low_level(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # the primitive cube is unwrapped by default, so we need not add a uv layer ourselves
        uv_proxy = blempy.LoopVectorAttributeProxy(
            obj.data, "uv_layers.active.data", "uv"
        )

        assert uv_proxy is not None
        # a cube has 6 faces and indices are stored as flattened arrays
        assert uv_proxy.loop_start.ndarray.shape == (6, )
        assert uv_proxy.loop_total.ndarray.shape == (6, )
        # 6 faces each have 4 loops (vertex corners)
        assert uv_proxy.loop_attributes.ndarray.shape == (24, 2)

        # retrieving data again should be no problem
        uv_proxy.get()

        # scale all uvs
        uv_proxy.loop_attributes.ndarray *= 0.5
        uv_proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = uv_proxy.loop_attributes.ndarray
        uv_proxy.loop_attributes.ndarray = None
        uv_proxy.get()
        assert np.allclose(original, uv_proxy.loop_attributes.ndarray)

    def test_vertex_color_layer_low_level(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # the primitive cube does not have a vertex color layer by default
        obj.data.vertex_colors.new()

        vcol_proxy = blempy.LoopVectorAttributeProxy(
            obj.data, "vertex_colors.active.data", "color"
        )

        assert vcol_proxy is not None
        # a cube has 6 faces and indices are stored as flattened arrays
        assert vcol_proxy.loop_start.ndarray.shape == (6, ) 
        assert vcol_proxy.loop_total.ndarray.shape == (6, )
        # 6 faces each have 4 loops (vertex corners) and vertex colors have 4 components
        assert vcol_proxy.loop_attributes.ndarray.shape == (24, 4)

        # a new vertex color layer is initialized to all white
        assert np.allclose(vcol_proxy.loop_attributes.ndarray, 1.0)

        # set all vertex colors to red
        vcol_proxy.loop_attributes.ndarray[:] = [1.0, 0.0, 0.0, 1.0]
        vcol_proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = vcol_proxy.loop_attributes.ndarray
        vcol_proxy.loop_attributes.ndarray = None
        vcol_proxy.get()
        assert np.allclose(original, vcol_proxy.loop_attributes.ndarray)

    def test_vertex_color_layer_iterator(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # the primitive cube does not have a vertex color layer by default
        obj.data.vertex_colors.new()

        vcol_proxy = blempy.LoopVectorAttributeProxy(
            obj.data, "vertex_colors.active.data", "color"
        )

        # cube has six faces
        assert len(vcol_proxy) == 6

        # test the iterator by setting all loops in each individual face to a distinct grey level
        # this will cause the face to have a uniform color
        for index, polygon_loops in enumerate(vcol_proxy):
            grey_level = index / 6
            polygon_loops[:] = [grey_level, grey_level, grey_level, 1.0]
        vcol_proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = vcol_proxy.loop_attributes.ndarray
        vcol_proxy.loop_attributes.ndarray = None
        vcol_proxy.get()

        # when assigning colors to a vertex color layer, Blender automatically gamma corrects those colors
        # so what we get back is *not* what we put in. What we can check is whether the original white 
        # values are replaced by something else
        assert np.all((original[:,:3] != 1).ravel())

    def test_color_attribute_layer_iterator(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # the primitive cube does not have a vertex color layer by default
        obj.data.vertex_colors.new(name="ACol")

        # this time we access the colors using the unified attribute layers
        # where color attribute layers have a color_srgb attribute that will
        # not be automatically gamma corrected (or only a little bit?)
        vcol_proxy = blempy.LoopVectorAttributeProxy(
            obj.data, "attributes['ACol']", "color_srgb"
        )

        # cube has six faces
        assert len(vcol_proxy) == 6

        # test the iterator by setting all loops in each individual face to a distinct grey level
        # this will cause the face to have a uniform color
        for index, polygon_loops in enumerate(vcol_proxy):
            grey_level = index / 6
            polygon_loops[:] = [grey_level, grey_level, grey_level, 1.0]
        vcol_proxy.set()

        # deliberately copy the original array
        # set it to None, and get them again to see if we indeed wrote them to the mesh
        original = vcol_proxy.loop_attributes.ndarray
        vcol_proxy.loop_attributes.ndarray = None
        vcol_proxy.get()

        # this is here to check iwhat the values are if they do not match
        # I still find it baffling that assigned values will be silently converted
        # but that is an issue regardless of this library.
        # for org,col in zip(original, vcol_proxy.loop_attributes.ndarray):
        #     print(f"{org} {col}")
        assert np.allclose(original, vcol_proxy.loop_attributes.ndarray, atol=0.01)

    def test_unified_attribute_color(self):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        # the primitive cube does not have a vertex color layer by default
        # so we add it using the old styl vertex_colors (but this will
        # show up in the unified attributes)
        obj.data.vertex_colors.new(name="ACol")

        # first a few negatives
        with pytest.raises(ValueError, match="unknown property"):
            proxy = blempy.AttributeProxy(obj.data, "UNKNOWN", "color_srgb")    
        with pytest.raises(ValueError, match="does not have an attribute"):
            proxy = blempy.AttributeProxy(obj.data, "ACol", "UNKNWON")    

        proxy = blempy.AttributeProxy(obj.data, "ACol", "color_srgb")

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
        proxy = blempy.AttributeProxy(obj.data, "UVMap")
        assert proxy.attr == "vector"

        # a plane has a single face
        assert len(proxy) == 1

        proxy.get()

        # get the first (and only) set of uv-coordinates
        uv_coordinates = proxy[0]  
        np.allclose(uv_coordinates, [[0,0],[1,0],[1,1],[0,1]])

        # scale them by a half and write back
        # uv_coordinates is a view, so no need to store it explicitly in the proxy
        uv_coordinates *= 0.5
        proxy.set()

        # force reload from mesh to check if put succeeded
        proxy.loop_attributes.ndarray = None
        proxy.get()

        uv_coordinates = proxy[0]  
        np.allclose(uv_coordinates, [[0,0],[.5,0],[.5, .5],[0,.5]])

        # cannot assign to a non existing face
        with pytest.raises(IndexError):
            proxy[1] = 0

        # but we can to an existing one (numpy will take care of converting the python list)
        proxy[0] = [[0,0],[1,0],[1,1],[0,1]]

        # force reload from mesh to check if put succeeded
        proxy.loop_attributes.ndarray = None
        proxy.get()

        uv_coordinates = proxy[0]  
        np.allclose(uv_coordinates, [[0,0],[1,0],[1,1],[0,1]])

