"""
ResearchOS Macro Intelligence Layer - Econometrics Matrix Algebra
Version: ecm/matrix/v1
Status: FROZEN

Minimal, deterministic linear algebra subset used by the Econometrics Engine.

Implementations are deliberately minimal (no external framework):
  - transpose
  - matrix multiplication
  - Gaussian elimination with column pivoting (solve)
  - matrix inversion (LU via Gaussian elimination)
  - identity

All functions are pure, deterministic, and stdlib-only. No numpy, no random,
no wall-clock dependence.

MIL-ECM-003: Matrix operations are deterministic and pure.
"""
from __future__ import annotations

from typing import List

Matrix = List[List[float]]


def transpose(matrix: Matrix) -> Matrix:
    """Return the transpose of a matrix (list of rows)."""
    if not matrix:
        return []
    n_cols = len(matrix[0])
    return [[matrix[r][c] for r in range(len(matrix))] for c in range(n_cols)]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    """
    Multiply two matrices.

    Args:
        a: Matrix of shape (m, n)
        b: Matrix of shape (n, p)

    Returns:
        Matrix of shape (m, p)
    """
    if not a or not b:
        return []
    m = len(a)
    n = len(a[0])
    p = len(b[0])
    if len(b) != n:
        raise ValueError(
            f"Incompatible dimensions for matmul: {len(a)}x{n} and {len(b)}x{p}"
        )
    bt = transpose(b)
    result = []
    for i in range(m):
        row = []
        ai = a[i]
        for j in range(p):
            bj = bt[j]
            total = 0.0
            for k in range(n):
                total += ai[k] * bj[k]
            row.append(total)
        result.append(row)
    return result


def identity(n: int) -> Matrix:
    """Return the n x n identity matrix."""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def _gauss_solve(a: Matrix, b: Matrix) -> Matrix:
    """
    Solve A X = B for X using Gaussian elimination with partial pivoting.

    Args:
        a: Square coefficient matrix (n x n).
        b: Right-hand side (n x k).

    Returns:
        Solution matrix X (n x k).

    Raises:
        ValueError: If the matrix is singular (no unique solution).
    """
    n = len(a)
    if n == 0:
        return []
    if len(b) != n:
        raise ValueError("b must have the same number of rows as a")

    # Augment [A | B]
    aug = [list(a[i]) + [b[i][j] for j in range(len(b[0]))] for i in range(n)]
    n_rhs = len(b[0])

    for col in range(n):
        # Partial pivoting: find the row with the largest absolute pivot.
        pivot = col
        max_val = abs(aug[col][col])
        for r in range(col + 1, n):
            v = abs(aug[r][col])
            if v > max_val:
                max_val = v
                pivot = r
        if max_val < 1e-12:
            raise ValueError("Singular matrix in Gaussian elimination")

        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_val = aug[col][col]
        # Normalize the pivot row.
        for j in range(col, n + n_rhs):
            aug[col][j] /= pivot_val

        # Eliminate below.
        for r in range(col + 1, n):
            factor = aug[r][col]
            if factor == 0.0:
                continue
            for j in range(col, n + n_rhs):
                aug[r][j] -= factor * aug[col][j]

    # Back substitution.
    x = [[0.0 for _ in range(n_rhs)] for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n):
            if aug[i][j] != 0.0:
                for k in range(n_rhs):
                    x[i][k] -= aug[i][j] * x[j][k]
        for k in range(n_rhs):
            x[i][k] += aug[i][n + k]

    return x


def solve(a: Matrix, b: List[float]) -> List[float]:
    """
    Solve A x = b for x (single right-hand side).

    Args:
        a: Square coefficient matrix (n x n).
        b: Right-hand side vector (length n).

    Returns:
        Solution vector (length n).
    """
    result = _gauss_solve(a, [[v] for v in b])
    return [row[0] for row in result]


def invert(a: Matrix) -> Matrix:
    """
    Invert a square matrix using Gaussian elimination.

    Args:
        a: Square matrix (n x n).

    Returns:
        Inverse matrix (n x n).

    Raises:
        ValueError: If the matrix is singular.
    """
    n = len(a)
    if n == 0:
        return []
    if any(len(row) != n for row in a):
        raise ValueError("Matrix must be square")
    ident = identity(n)
    return _gauss_solve(a, ident)


def determinant(a: Matrix) -> float:
    """
    Compute the determinant of a square matrix via Gaussian elimination.

    Args:
        a: Square matrix (n x n).

    Returns:
        Determinant value.
    """
    n = len(a)
    if n == 0:
        return 1.0
    if any(len(row) != n for row in a):
        raise ValueError("Matrix must be square")
    work = [list(row) for row in a]
    det = 1.0
    for col in range(n):
        pivot = col
        max_val = abs(work[col][col])
        for r in range(col + 1, n):
            v = abs(work[r][col])
            if v > max_val:
                max_val = v
                pivot = r
        if max_val < 1e-12:
            return 0.0
        if pivot != col:
            work[col], work[pivot] = work[pivot], work[col]
            det = -det
        pivot_val = work[col][col]
        det *= pivot_val
        for r in range(col + 1, n):
            factor = work[r][col] / pivot_val
            if factor == 0.0:
                continue
            for j in range(col, n):
                work[r][j] -= factor * work[col][j]
    return det


__all__ = [
    "Matrix",
    "transpose",
    "matmul",
    "identity",
    "solve",
    "invert",
    "determinant",
]
