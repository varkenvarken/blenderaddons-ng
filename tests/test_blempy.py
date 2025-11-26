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
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=1)
        bpy.ops.object.mode_set(mode='OBJECT')

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
        test_proxy.ndarray[:,2] += 1
        assert np.allclose(test_proxy.ndarray, cube + [0,0,1])

        # copy it back
        test_proxy.set()

        # deliberately deallocate the original array and then retrieve the vertex data again
        test_proxy.ndarray = None
        test_proxy.get()

        # it should match the moved coordinates
        assert np.allclose(test_proxy.ndarray, cube + [0,0,1])

    def test_vertex_co_property_matmul_rotate3(self, cube, identity3):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

        test_proxy.get()

        # mutliplication by the identity matrix should not change anything
        result = test_proxy @ identity3
        assert result is test_proxy  # multiplication is in place, i.e. left hand side is returned
        assert np.allclose(result.ndarray, cube)

        # rotate all vertice 45 degrees around the z-axis
        rot_z_45deg = Matrix.Rotation(pi/4, 3, [0,0,1])
        result = test_proxy @ rot_z_45deg

        # compare to the list of vertices rotated one by one
        s = sin(pi/4)
        c = cos(pi/4)
        cube_rotated = [[v[0]*c-v[1]*s, v[0]*s+v[1]*c, v[2] ] for v in cube]
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
        assert np.allclose(test_proxy.ndarray[:,:3], cube)
        # and the 4th dimension should be all ones
        assert np.allclose(test_proxy.ndarray[:,3], 1)

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
        assert np.allclose(test_proxy.ndarray[:,:3], cube)
        # but the 4th dimension should be all zeros
        assert np.allclose(test_proxy.ndarray[:,3], 0)

    def test_vertex_co_property_matmul_rotate4(self, cube, identity4):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

        test_proxy.get()
        test_proxy.extend()

        # mutliplication by the identity matrix should not change anything
        result = test_proxy @ identity4
        assert result is test_proxy  # multiplication is in place, i.e. left hand side is returned
        assert np.allclose(result.ndarray[:,:3], cube)

        # rotate all vertice 45 degrees around the z-axis
        rot_z_45deg = Matrix.Rotation(pi/4, 4, [0,0,1])
        result = test_proxy @ rot_z_45deg

        # compare to the list of vertices rotated one by one
        s = sin(pi/4)
        c = cos(pi/4)
        cube_rotated = [[v[0]*c-v[1]*s, v[0]*s+v[1]*c, v[2] ] for v in cube]
        np.allclose(result.ndarray[:,:3], cube_rotated)

    def test_vertex_co_property_matmul_translate4(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

        test_proxy.get()
        test_proxy.extend()

        # translate 1 unit along the z-axis
        rot_z_45deg = Matrix.Translation([0,0,1])
        result = test_proxy @ rot_z_45deg

        # check that the matrix multiplication in this case is identical to a direct translation
        np.allclose(result.ndarray[:,:3], cube + [0,0,1])

    def test_vertex_co_property_empty_mesh(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")
        # not empty, but forgetting to retrieve the actual data will also prevent a discard
        with pytest.raises(ValueError):
            test_proxy.discard()

        # remove all vertices from the primitive cube
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete()
        bpy.ops.object.mode_set(mode='OBJECT')

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

        with pytest.raises(ValueError):
            test_proxy.get()
    
        with pytest.raises(ValueError):
            test_proxy.set()

        with pytest.raises(ValueError):
            test_proxy.extend()

        with pytest.raises(ValueError):
            test_proxy.discard()

    def test_vertex_co_property_extend_no_data(self, cube):
        # Create a new object and set as active
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

        test_proxy = blempy.VectorCollectionProxy(obj.data, "vertices", "co")

        # extend without get should raise an exception
        with pytest.raises(ValueError):
            test_proxy.extend()

        # the primitive cube has a default uv layer. uv layers are two dimensional, so we do not allow extension, nor discarding
        test_proxy = blempy.VectorCollectionProxy(obj.data.uv_layers.active, "uv", "vector")
        test_proxy.get()
        with pytest.raises(ValueError):
            test_proxy.extend()
        with pytest.raises(ValueError):
            test_proxy.discard()