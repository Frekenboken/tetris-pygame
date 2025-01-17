import numpy as np

def rotate_matrix(matrix):
    return np.rot90(matrix, k=-1).tolist()