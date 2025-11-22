from time import time
from timeit import Timer
import numpy as np

T = np.dtype[np.float32]
VEC3 = np.ndarray[tuple[1, 3], T]
MAT3x3 = np.ndarray[tuple[3, 3], T]

# see: https://en.wikipedia.org/wiki/Matrix_multiplication

# note: newer versions of Numpy also have np.matvec() and np.vecmat() functions
# that can multiply stacks of vectors but because Blender 5.0 uses numpy 1.26.4
# we cannot use them here.


def multiply_vector_matrix(x: VEC3, a: MAT3x3) -> VEC3:
    """
    Multiply a column vector X with a matrix A.

    Y_i = SUM_j (A_ij * X_j)
    """
    y: VEC3 = np.ndarray(3, dtype=np.float32)
    for i in range(3):
        y[i] = 0
        for j in range(3):
            y[i] += a[i, j] * x[j]
    return y


def multiply_matrix_vector(a: MAT3x3, x: VEC3) -> VEC3:
    """
    Multiply a matrix A with a row vector X.

    Y_k = SUM_j (A_jk * X_j)
    """
    y: VEC3 = np.ndarray(3, dtype=np.float32)
    for k in range(3):
        y[k] = 0
        for j in range(3):
            y[k] += a[j, k] * x[j]
    return y


def multiply_vector_matrix_comprehension(x: VEC3, a: MAT3x3) -> VEC3:
    """
    Multiply a column vector X with a matrix A.

    Y_i = SUM_j (A_ij * X_j)
    """
    y: VEC3 = np.ndarray(3, dtype=np.float32)
    for i in range(3):
        y[i] = sum(a[i, j] * x[j] for j in range(3))
    return y


def multiply_matrix_vector_comprehension(a: MAT3x3, x: VEC3) -> VEC3:
    """
    Multiply a matrix A with a row vector X.

    Y_k = SUM_j (A_jk * X_j)
    """
    y: VEC3 = np.ndarray(3, dtype=np.float32)
    for k in range(3):
        y[k] = sum(a[j, k] * x[j] for j in range(3))
    return y


def multiply_vector_matrix_np_dot(x: VEC3, a: MAT3x3) -> VEC3:
    """
    Multiply a column vector X with a matrix A.

    Y_i = SUM_j (A_ij * X_j)
    """
    return np.dot(a, x)


def multiply_matrix_vector_np_dot(a: MAT3x3, x: VEC3) -> VEC3:
    """
    Multiply a matrix A with a row vector X.

    Y_k = SUM_j (A_jk * X_j)
    """
    y: VEC3 = np.ndarray(3, dtype=np.float32)
    return np.dot(x, a)


def multiply_vector_matrix_array_np_dot(x, a: MAT3x3):
    """
    Multiply a list of column vectors X with matrix A.
    """
    return np.dot(a, x.reshape(-1, 3, 1)).T


def multiply_matrix_vector_array_np_dot(a: MAT3x3, x):
    """
    Multiply a list of row vectors X with matrix A.
    """
    return np.dot(x, a)


def multiply_matrix_vector_array_np_einsum(a: MAT3x3, x):
    """
    Multiply a list of row vectors X with matrix A.
    """
    return np.einsum("ij,jk->ik", x, a)


def multiply_vector_matrix_array_np_dot_in_place(a: MAT3x3, x):
    """
    Multiply a list of row vectors X with matrix A.
    """
    x = np.dot(x, a, out=x)
    # x = x.T
    return x


vectors = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)

matrices = np.array(
    [
        # 90 degrees counter clockwise around z-axis
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
        # 45 degrees counter clockwise around z-axis
        [
            [0.7071068286895752, 0.7071068286895752, 0.0],
            [-0.7071068286895752, 0.7071068286895752, 0.0],
            [0.0, 0.0, 1.0],
        ],
    ],
    dtype=np.float32,
)

results_row = np.array(
    [
        [[0, 1, 0], [-1, 0, 0]],
        [
            [0.7071068286895752, 0.7071068286895752, 0.0],
            [-0.7071068286895752, 0.7071068286895752, 0.0],
        ],
    ],
    dtype=np.float32,
)

results_col = np.array(
    [
        [[0, -1, 0], [1, 0, 0]],
        [
            [0.7071068286895752, -0.7071068286895752, 0.0],
            [0.7071068286895752, 0.7071068286895752, 0.0],
        ],
    ],
    dtype=np.float32,
)


class TestMatrixMultiplication:
    def test_python_naive(self):
        for mi, matrix in enumerate(matrices):
            for vi, vector in enumerate(vectors):
                result = multiply_matrix_vector(matrix, vector)
                assert np.allclose(result, results_row[mi, vi])
                result = multiply_vector_matrix(vector, matrix)
                assert np.allclose(result, results_col[mi, vi])

    def test_python_comprehension(self):
        for mi, matrix in enumerate(matrices):
            for vi, vector in enumerate(vectors):
                result = multiply_matrix_vector_comprehension(matrix, vector)
                assert np.allclose(result, results_row[mi, vi])
                result = multiply_vector_matrix_comprehension(vector, matrix)
                assert np.allclose(result, results_col[mi, vi])

    def test_numpy_dot(self):
        for mi, matrix in enumerate(matrices):
            for vi, vector in enumerate(vectors):
                result = multiply_matrix_vector_np_dot(matrix, vector)
                assert np.allclose(result, results_row[mi, vi])
                result = multiply_vector_matrix_np_dot(vector, matrix)
                assert np.allclose(result, results_col[mi, vi])

    def test_numpy_dot_list(self):
        for matrix, expected_result in zip(matrices, results_row):
            results = multiply_matrix_vector_array_np_dot(matrix, vectors)
            assert np.allclose(results, expected_result)
        for matrix, expected_result in zip(matrices, results_col):
            results = multiply_vector_matrix_array_np_dot(vectors, matrix)
            assert np.allclose(results, expected_result)

    def test_numpy_einsum_list(self):
        for matrix, expected_result in zip(matrices, results_row):
            results = multiply_matrix_vector_array_np_einsum(matrix, vectors)
            assert np.allclose(results, expected_result)

    def test_numpy_dot_list_in_place(self):
        for matrix, expected_result in zip(matrices, results_row):
            results = multiply_vector_matrix_array_np_dot_in_place(
                matrix, vectors.copy()
            )  # we perform the op in-place, so for these individual tests we have to copy it because otherwise our test data gets messed up (prob. have to change this to a fixture)
            assert np.allclose(results, expected_result)


if __name__ == "__main__":
    vector = np.array([1, 0, 0], dtype=np.float32)
    matrix = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=np.float32)

    sizes = (1, 2, 5, 10)
    vsizes = (1, 2, 5, 10, 20, 50, 100)
    repeats = 5

    width = 50
    print()
    print(f"{'function':{width}s},  seconds elapsed (lower is better)")
    print(
        f"{'number of vectors':{width}s},{','.join(f'{str(s * 100_000):>8s}' for s in vsizes)}"
    )

    for function in (
        multiply_matrix_vector,
        multiply_matrix_vector_comprehension,
        multiply_matrix_vector_np_dot,
    ):
        print(f"\n{function.__name__:{width}s},", end="")

        for factor in sizes:
            ops = factor * 100_000
            multiplier = 10 / factor

            timer = Timer(f"{function.__name__}(matrix, vector)", globals=globals())
            t = timer.timeit(ops)
            print(f"{t:8.4f},", end="")

    for function in (
        multiply_matrix_vector_array_np_dot,
        multiply_matrix_vector_array_np_einsum,
        multiply_vector_matrix_array_np_dot_in_place,
    ):
        print(f"\n{function.__name__:{width}s},", end="")

        for factor in vsizes:
            ops = factor * 100_000
            multiplier = 10 / factor

            t = 0.0
            for r in range(repeats):
                vectors = np.random.random(3 * ops).reshape(-1, 3)

                start = time()
                function(matrix, vectors)
                t += time() - start
            print(f"{t/repeats:8.4f},", end="")

    print("\n")
