import numpy as np
import euklid

from openglider.vector.functions import norm, normalize
from openglider.vector.polyline import PolyLine2D


def point2d(p1_3d, p1_2d, p2_3d, p2_2d, point_3d):
    """Returns a third points position relative to two known points (3D+2D)"""
    # diffwise
    diff_3d = (p2_3d - p1_3d).normalized()
    diff_2d = (p2_2d - p1_2d).normalized()

    diff_point = point_3d-p1_3d
    point_2d = p1_2d + diff_2d * diff_3d.dot(diff_point)
    # length-wise
    diff_3d = (diff_point - diff_3d * diff_3d.dot(diff_point)).normalized()
    #diff_2d = diff_2d.dot([[0, 1], [-1, 0]])  # Rotate 90deg
    diff_2d = euklid.vector.Vector2D([diff_2d[1], -diff_2d[0]])
    return point_2d + diff_2d * diff_3d.dot(diff_point)


def flatten_list(list1, list2):
    if not isinstance(list1, euklid.vector.PolyLine3D):
        list1 = euklid.vector.PolyLine2D(list1.data.tolist())
    if not isinstance(list2, euklid.vector.PolyLine3D):
        list2 = euklid.vector.PolyLine2D(list2.data.tolist())

    list1 = list1.nodes
    list2 = list2.nodes
    index_left = index_right = 0
    flat_left = [euklid.vector.Vector2D([0, 0])]
    flat_right = [euklid.vector.Vector2D([(list1[0]-list2[0]).length(), 0])]

    # def which(i, j):
    #     diff = list1[i] - list2[j]
    #     return diff.dot(list1[i+1]-list1[i]+list2[j+1]-list2[j+1])
    while True:
        #while which(index_left, index_right) <= 0 and index_left < len(list1) - 2:  # increase left_index
        if index_left < len(list1) - 1:
            flat_left.append(point2d(list1[index_left], flat_left[index_left],
                                     list2[index_right], flat_right[index_right],
                                     list1[index_left + 1]))
            index_left += 1

        #while which(index_left, index_right) >= 0 and index_right < len(list2) - 2:  # increase right_index
        if index_right < len(list2) - 1:
            flat_right.append(point2d(list1[index_left], flat_left[index_left],
                                      list2[index_right], flat_right[index_right],
                                      list2[index_right + 1]))
            index_right += 1

        if index_left == len(list1) - 1 and index_right == len(list2) - 1:
            break

    # while index_left < len(list1) - 1:
    #     flat_left.append(point2d(list1[index_left], flat_left[index_left],
    #                              list2[index_right], flat_right[index_right],
    #                              list1[index_left + 1]))
    #     index_left += 1
    #
    # while index_right < len(list2) - 1:
    #     flat_right.append(point2d(list1[index_left], flat_left[index_left],
    #                               list2[index_right], flat_right[index_right],
    #                               list2[index_right + 1]))
    #     index_right += 1

    return euklid.vector.PolyLine2D(flat_left), euklid.vector.PolyLine2D(flat_right)