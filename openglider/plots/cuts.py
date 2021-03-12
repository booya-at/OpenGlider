import math

import euklid

from openglider.vector.functions import normalize, rotation_2d


class CutResult():
    def __init__(self, curve, index_left, index_right, inner_indices):
        self.curve = curve
        self.index_left = index_left
        self.index_right = index_right
        self.inner_indices = inner_indices


###############CUTS####################
# Check doc/drawings 7-9 for sketches
# DESIGN-CUT Style
class DesignCut(object):
    def __init__(self, amount, num_folds=1):
        self.amount = amount * num_folds

    @classmethod
    def __json__(cls):
        return {}

    @classmethod
    def __from_json__(cls, **kwargs):
        return cls

    def get_p1_p2(self, inner_lists, amount_3d):
        l1, ik1 = inner_lists[0]
        l2, ik2 = inner_lists[-1]

        if amount_3d is not None:
            ik1_new = l1.walk(ik1, amount_3d[0])
            ik2_new = l2.walk(ik2, amount_3d[-1])

            return l1.get(ik1_new), l2.get(ik2_new)

        return l1.get(ik1), l2.get(ik2)


    def _get_indices(self, inner_lists, amount_3d):
        indices = []
        for i, lst in enumerate(inner_lists):
            line, ik = lst
            if amount_3d is not None:
                ik = line.walk(ik, amount_3d[i])

            indices.append(ik)

        return indices

    def apply(self, inner_lists, outer_left, outer_right, amount_3d=None):
        #p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
        #p2 = inner_lists[-1][0][inner_lists[-1][1]]
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)
        
        normvector = euklid.vector.Vector2D(list(rotation_2d(math.pi/2).dot(p1-p2))).normalized()

        newlist = []
        # todo: sort by distance
        cuts_left = outer_left.cut(p1, p2)
        cuts_left.sort(key=lambda cut: -abs(cut[1]))
        leftcut_index = cuts_left[0][0]
        leftcut = outer_left.get(leftcut_index)

        newlist.append(leftcut)
        newlist.append(leftcut+normvector*self.amount)

        for thislist in inner_lists:
            newlist.append(thislist[0].get(thislist[1]) + normvector*self.amount)

        cuts_right = outer_right.cut(p1, p2)
        cuts_right.sort(key=lambda cut: abs(cut[1]))
        rightcut_index = cuts_right[0][0]
        rightcut = outer_right.get(rightcut_index)

        newlist.append(rightcut+normvector*self.amount)
        newlist.append(rightcut)

        curve = euklid.vector.PolyLine2D(newlist)

        return CutResult(curve, leftcut_index, rightcut_index, indices)


class SimpleCut(DesignCut):
    def apply(self, inner_lists, outer_left, outer_right, amount_3d=None):
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)

        normvector = euklid.vector.Vector2D(list(rotation_2d(math.pi/2).dot(p1-p2))).normalized()

        leftcut_index = outer_left.cut(p1, p2, inner_lists[0][1])
        rightcut_index = outer_right.cut(p1, p2, inner_lists[-1][1])

        index_left = leftcut_index[0]
        index_right = rightcut_index[0]

        leftcut = outer_left.get(index_left)
        rightcut = outer_right.get(index_right)

        leftcut_index_2 = outer_left.cut(p1 - normvector * self.amount, p2 - normvector * self.amount, inner_lists[0][1])
        rightcut_index_2 = outer_right.cut(p1 - normvector * self.amount, p2 - normvector * self.amount, inner_lists[-1][1])

        leftcut_2 = outer_left.get(leftcut_index_2[0])
        rightcut_2 = outer_right.get(rightcut_index_2[0])
        diff_l, diff_r = leftcut-leftcut_2, rightcut - rightcut_2

        curve = euklid.vector.PolyLine2D([leftcut, leftcut+diff_l, rightcut+diff_r, rightcut])

        return CutResult(curve, leftcut_index[0], rightcut_index[0], indices)


class Cut3D(DesignCut):
    def apply(self, inner_lists, outer_left: euklid.vector.PolyLine2D, outer_right: euklid.vector.PolyLine2D, amount_3d=None):
        """

        :param inner_lists:
        :param outer_left:
        :param outer_right:
        :param amount_3d: list of 3d-shaping amounts
        :return:
        """
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        normvector = euklid.vector.Vector2D(list(rotation_2d(math.pi/2).dot(p1-p2))).normalized()

        inner_ik = []
        point_list = []

        for offset, lst in zip(amount_3d, inner_lists):
            curve, ik = lst
            ik_new = curve.walk(ik, offset)
            inner_ik.append(ik_new)

            sewing_mark_point = curve.get(ik_new)
            point_list.append(sewing_mark_point + normvector*self.amount)

        left_1 = point_list[0]
        left_2 = point_list[1]
        left_ik = inner_ik[0]

        right_1 = point_list[-2]
        right_2 = point_list[-1]
        right_ik = inner_ik[-1]

        leftcut_index, _ = outer_left.cut(left_1, left_2, left_ik)
        rightcut_index, _ = outer_right.cut(right_1, right_2, right_ik)

        curve = euklid.vector.PolyLine2D(point_list)

        return CutResult(curve, leftcut_index, rightcut_index, inner_ik)

class Cut3D_2(DesignCut):
    def apply(self, inner_lists, outer_left, outer_right, amount_3d=None):
        """

        :param inner_lists:
        :param outer_left:
        :param outer_right:
        :param amount_3d: list of 3d-shaping amounts
        :return:
        """

        inner_new = []
        point_list = []

        for offset, lst in zip(amount_3d, inner_lists):
            curve, ik = lst
            ik_new = curve.walk(ik, offset)
            inner_new.append([curve, ik_new])

        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        normvector = euklid.vector.Vector2D(list(rotation_2d(math.pi/2).dot(p1-p2))).normalized()

        leftcut_index = outer_left.cut(p1, p2, inner_lists[0][1])
        rightcut_index = outer_right.cut(p1, p2, inner_lists[-1][1])

        index_left = leftcut_index[0]
        index_right = rightcut_index[0]

        leftcut = outer_left.get(index_left)
        rightcut = outer_right.get(index_right)

        point_list.append(leftcut)
        point_list.append(leftcut+normvector*self.amount)

        for curve, ik in inner_new:
            point_list.append(curve.get(ik) + normvector*self.amount)

        point_list.append(rightcut+normvector*self.amount)
        point_list.append(rightcut)

        curve = euklid.vector.PolyLine2D(point_list)

        return CutResult(curve, index_left, index_right, [x[1] for x in inner_new])


# OPEN-ENTRY Style
class FoldedCut(DesignCut):
    def __init__(self, amount, num_folds=2):
        self.num_folds = num_folds
        super(FoldedCut, self).__init__(amount)

    def apply(self, inner_lists, outer_left, outer_right, amount_3d=None):
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)

        normvector = euklid.vector.Vector2D(list(rotation_2d(math.pi/2).dot(p1-p2))).normalized()

        left_start_index = outer_left.cut(p1, p2, inner_lists[0][1])[0]
        right_start_index = outer_right.cut(p1, p2, inner_lists[-1][1])[0]

        pp1 = p1 - normvector * self.amount
        pp2 = p2 - normvector * self.amount
        left_end_index = outer_left.cut(pp1, pp2, inner_lists[0][1])[0]
        right_end_index = outer_right.cut(pp1, pp2, inner_lists[-1][1])[0]

        left_start = outer_left.get(left_start_index)
        left_end = outer_left.get(left_end_index)
        right_start = outer_right.get(right_start_index)
        right_end = outer_right.get(right_end_index)

        left_piece = outer_left.get(left_end_index, left_start_index)
        right_piece = outer_right.get(right_end_index, right_start_index)
        left_piece_mirrored = left_piece.mirror(p1, p2)
        right_piece_mirrored = right_piece.mirror(p1, p2)

        # mirror to (p1-p2) -> p'=p-2*(p.normvector)
        last_left, last_right = left_start, right_start
        new_left, new_right = euklid.vector.PolyLine2D([]), euklid.vector.PolyLine2D([])

        for i in range(self.num_folds):
            left_this = left_piece if i % 2 else left_piece_mirrored
            right_this = right_piece if i % 2 else right_piece_mirrored
            new_left = new_left + left_this.move(last_left-left_this.get(0))
            new_right = new_right + right_this.move(last_right-right_this.get(0))
            last_left = new_left.get(len(new_left)-1)
            last_right = new_right.get(len(new_right)-1)

        curve = new_left+new_right.reverse()

        return CutResult(curve, left_start_index, right_start_index, indices)


# TRAILING-EDGE Style
class ParallelCut(DesignCut):
    """
    Cut to continue in a parallel way (trailing-edge)
    """
    def apply(self, inner_lists, outer_left, outer_right, amount_3d=None):
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)

        normvector = euklid.vector.Vector2D(list(rotation_2d(math.pi/2).dot(p1-p2))).normalized()

        leftcut_index = outer_left.cut(p1, p2, inner_lists[0][1])
        rightcut_index = outer_right.cut(p1, p2, inner_lists[-1][1])

        index_left = leftcut_index[0]
        index_right = rightcut_index[0]

        leftcut = outer_left.get(index_left)
        rightcut = outer_right.get(index_right)

        leftcut_index_2 = outer_left.cut(p1 - normvector * self.amount, p2 - normvector * self.amount, inner_lists[0][1])
        rightcut_index_2 = outer_right.cut(p1 - normvector * self.amount, p2 - normvector * self.amount, inner_lists[-1][1])

        leftcut_2 = outer_left.get(leftcut_index_2[0])
        rightcut_2 = outer_right.get(rightcut_index_2[0])
        diff = (leftcut-leftcut_2 + rightcut - rightcut_2) * 0.5

        curve = euklid.vector.PolyLine2D([leftcut, leftcut+diff, rightcut+diff, rightcut])

        #iks = [x[1] for x in inner_lists]

        #iks[0] = inner_lists[0][0].walk()

        return CutResult(curve, leftcut_index[0], rightcut_index[0], indices)


# TODO: used?
cuts = {"orthogonal": DesignCut,
        "folded": FoldedCut,
        "parallel": ParallelCut}