
import numpy
from openglider.Vector import Vectorlist2D, norm, normalize


def flatten_list(list1, list2):
    index_left = index_right = 0
    flat_left = [numpy.array([0, 0])]
    flat_right = [numpy.array([norm(list1[0]-list2[0]), 0])]

    def which(i, j):
        diff = list1[i] - list2[j]
        return diff.dot(list1[i+1]-list1[i]+list2[j+1]-list2[j+1])

    def point2d(p1_3d, p1_2d, p2_3d, p2_2d, point_3d):
        # diffwise
        diff_3d = normalize(p2_3d - p1_3d)
        diff_2d = normalize(p2_2d - p1_2d)
        diff_point = point_3d-p1_3d
        point_2d = p1_2d + diff_2d * diff_3d.dot(diff_point)
        # length-wise
        diff_3d = normalize(diff_point - diff_3d * diff_3d.dot(diff_point))
        diff_2d = diff_2d.dot([[0, 1], [-1, 0]])  # Rotate 90deg

        return numpy.array(point_2d + diff_2d * diff_3d.dot(diff_point))

    while True:
        #while which(index_left, index_right) <= 0 and index_left < len(list1) - 2:  # increase left_index
        flat_left.append(point2d(list1[index_left], flat_left[index_left],
                                 list2[index_right], flat_right[index_right],
                                 list1[index_left + 1]))
        index_left += 1

        #while which(index_left, index_right) >= 0 and index_right < len(list2) - 2:  # increase right_index
        flat_right.append(point2d(list1[index_left], flat_left[index_left],
                                  list2[index_right], flat_right[index_right],
                                  list2[index_right + 1]))
        index_right += 1

        if index_left == len(list1) - 2 or index_right == len(list2) - 2:
            break

    while index_left < len(list1) - 1:
        flat_left.append(point2d(list1[index_left], flat_left[index_left],
                                 list2[index_right], flat_right[index_right],
                                 list1[index_left + 1]))
        index_left += 1

    while index_right < len(list2) - 1:
        flat_right.append(point2d(list1[index_left], flat_left[index_left],
                                  list2[index_right], flat_right[index_right],
                                  list2[index_right + 1]))
        index_right += 1


    return flat_left, flat_right