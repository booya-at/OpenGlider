from abc import ABC
import math
import logging
import euklid

from openglider.utils.dataclass import BaseModel
from openglider.vector.unit import Length
from pydantic import ConfigDict


logger = logging.getLogger(__name__)


class CutResult(BaseModel):
    curve: euklid.vector.PolyLine2D
    index_left: float
    index_right: float
    inner_indices: list[float]

    def __init__(self, curve: euklid.vector.PolyLine2D, index_left: float, index_right: float, inner_indices: list[float]):
        # WHY????
        super().__init__(  # type: ignore
            curve=curve,
            index_left = index_left,
            index_right = index_right,
            inner_indices = inner_indices
        )

InnerLists = list[tuple[euklid.vector.PolyLine2D, float]]

class Cut(ABC, BaseModel):
    amount: Length

    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:

        raise NotImplementedError()


# Check doc/drawings 7-9 for sketches


class DesignCut(Cut):
    num_folds: int = 1
    # model_config = ConfigDict(kw_only=False) TODO: kw_only needed?
    
    @property
    def total_amount(self) -> float:
        return self.num_folds * float(self.amount)

    def get_p1_p2(self, inner_lists: InnerLists, amount_3d: list[float] | None) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        l1, ik1 = inner_lists[0]
        l2, ik2 = inner_lists[-1]

        if amount_3d is not None:
            ik1_new = l1.walk(ik1, amount_3d[0])
            ik2_new = l2.walk(ik2, amount_3d[-1])

            return l1.get(ik1_new), l2.get(ik2_new)

        return l1.get(ik1), l2.get(ik2)


    def _get_indices(self, inner_lists: InnerLists, amount_3d: list[float] | None) -> list[float]:
        indices = []
        for i, lst in enumerate(inner_lists):
            line, ik = lst
            if amount_3d is not None:
                ik = line.walk(ik, amount_3d[i])

            indices.append(ik)

        return indices

    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:

        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)
        
        normvector = euklid.vector.Rotation2D(-math.pi/2).apply(p1-p2).normalized()

        newlist = []
        # todo: sort by distance
        cuts_left = outer_left.cut(p1, p2)
        cuts_left.sort(key=lambda cut: -abs(cut[1]))
        leftcut_index = cuts_left[0][0]
        leftcut = outer_left.get(leftcut_index)

        newlist.append(leftcut)
        newlist.append(leftcut+normvector*self.total_amount)

        for thislist in inner_lists:
            newlist.append(thislist[0].get(thislist[1]) + normvector*self.total_amount)

        cuts_right = outer_right.cut(p1, p2)
        cuts_right.sort(key=lambda cut: abs(cut[1]))
        rightcut_index = cuts_right[0][0]
        rightcut = outer_right.get(rightcut_index)

        newlist.append(rightcut+normvector*self.total_amount)
        newlist.append(rightcut)

        curve = euklid.vector.PolyLine2D(newlist)

        return CutResult(curve, leftcut_index, rightcut_index, indices)


class SimpleCut(DesignCut):
    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:

        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)

        normvector = euklid.vector.Rotation2D(-math.pi/2).apply(p1-p2).normalized()

        # TODO: fix in euklid!
        try:
            leftcut_index = outer_left.cut(p1, p2, inner_lists[0][1])
            index_left = leftcut_index[0]
        except RuntimeError:
            logger.error(f"no cut found")
            index_left = inner_lists[0][1]

        try:
            rightcut_index = outer_right.cut(p1, p2, inner_lists[-1][1])
            index_right = rightcut_index[0]
        except RuntimeError:
            logger.error(f"no cut found")
            index_right = inner_lists[-1][1]


        leftcut = outer_left.get(index_left)
        rightcut = outer_right.get(index_right)

        leftcut_index_2 = outer_left.cut(p1 - normvector * self.total_amount, p2 - normvector * self.total_amount, inner_lists[0][1])
        rightcut_index_2 = outer_right.cut(p1 - normvector * self.total_amount, p2 - normvector * self.total_amount, inner_lists[-1][1])

        leftcut_2 = outer_left.get(leftcut_index_2[0])
        rightcut_2 = outer_right.get(rightcut_index_2[0])
        diff_l, diff_r = leftcut-leftcut_2, rightcut - rightcut_2

        curve = euklid.vector.PolyLine2D([leftcut, leftcut+diff_l, rightcut+diff_r, rightcut])

        return CutResult(curve, index_left, index_right, indices)


class Cut3D(DesignCut):
    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:
        
        """
        :param inner_lists:
        :param outer_left:
        :param outer_right:
        :param amount_3d: list of 3d-shaping amounts
        :return:
        """

        inner_ik = []
        inner_points = []

        if amount_3d is None:
            amount_3d = [0] * len(inner_lists)

        for offset, lst in zip(amount_3d, inner_lists):
            curve, ik = lst
            ik_new = curve.walk(ik, offset)
            inner_ik.append(ik_new)
            inner_points.append(curve.get(ik_new))
        
        inner_curve = euklid.vector.PolyLine2D(inner_points)
        normvectors = inner_curve.normvectors()

        curve = inner_curve.add(normvectors * -self.total_amount)



        #    sewing_mark_point = curve.get(ik_new)
        #point_list.append(sewing_mark_point + normvector*self.total_amount)

        left_1 = curve.nodes[0]
        left_2 = curve.nodes[1]
        left_ik = inner_ik[0]

        right_1 = curve.nodes[-1]
        right_2 = curve.nodes[-2]
        right_ik = inner_ik[-1]

        try:
            leftcut_index, _ = outer_left.cut(left_1, left_2, left_ik)
        except:
            leftcut_index = left_ik
        
        try:
            rightcut_index, _ = outer_right.cut(right_1, right_2, right_ik)
        except:
            rightcut_index = right_ik

        

        #curve = euklid.vector.PolyLine2D(point_list)

        return CutResult(curve, leftcut_index, rightcut_index, inner_ik)

class Cut3D_2(DesignCut):
    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:
        
        """

        :param inner_lists:
        :param outer_left:
        :param outer_right:
        :param amount_3d: list of 3d-shaping amounts
        :return:
        """
        inner_new = []
        point_list = []
        
        if amount_3d is None:
            amount_3d = [0] * len(inner_lists)

        for offset, lst in zip(amount_3d, inner_lists):
            curve, ik = lst
            ik_new = curve.walk(ik, offset)
            inner_new.append((curve, ik_new))

        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        normvector = euklid.vector.Rotation2D(-math.pi/2).apply(p1-p2).normalized()

        leftcut_index = outer_left.cut(p1, p2, inner_lists[0][1])
        rightcut_index = outer_right.cut(p1, p2, inner_lists[-1][1])

        index_left = leftcut_index[0]
        index_right = rightcut_index[0]

        leftcut = outer_left.get(index_left)
        rightcut = outer_right.get(index_right)

        point_list.append(leftcut)
        point_list.append(leftcut+normvector*self.total_amount)

        for curve, ik in inner_new:
            point_list.append(curve.get(ik) + normvector*self.total_amount)

        point_list.append(rightcut+normvector*self.total_amount)
        point_list.append(rightcut)

        curve = euklid.vector.PolyLine2D(point_list)

        return CutResult(curve, index_left, index_right, [x[1] for x in inner_new])


# OPEN-ENTRY Style
class FoldedCut(DesignCut):
    num_folds: int = 2

    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:
        
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)

        normvector = euklid.vector.Rotation2D(-math.pi/2).apply(p1-p2).normalized()

        left_start_index = outer_left.cut(p1, p2, inner_lists[0][1])[0]
        right_start_index = outer_right.cut(p1, p2, inner_lists[-1][1])[0]

        p1_with_offset = p1 - normvector * self.total_amount
        p2_with_offset = p2 - normvector * self.total_amount
        left_end_index = outer_left.cut(p1_with_offset, p2_with_offset, inner_lists[0][1])[0]
        right_end_index = outer_right.cut(p1_with_offset, p2_with_offset, inner_lists[-1][1])[0]

        left_start = outer_left.get(left_start_index)
        right_start = outer_right.get(right_start_index)

        left_piece = outer_left.get(left_end_index, left_start_index)
        right_piece = outer_right.get(right_end_index, right_start_index)
        left_piece_mirrored = left_piece.mirror(p1, p2).reverse()
        right_piece_mirrored = right_piece.mirror(p1, p2).reverse()

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
    def apply(
        self,
        inner_lists: InnerLists,
        outer_left: euklid.vector.PolyLine2D,
        outer_right: euklid.vector.PolyLine2D,
        amount_3d: list[float] | None=None
        ) -> CutResult:
        
        p1, p2 = self.get_p1_p2(inner_lists, amount_3d)
        indices = self._get_indices(inner_lists, amount_3d)

        normvector = euklid.vector.Rotation2D(-math.pi/2).apply(p1-p2).normalized()

        leftcut_index = outer_left.cut(p1, p2, inner_lists[0][1])
        rightcut_index = outer_right.cut(p1, p2, inner_lists[-1][1])

        index_left = leftcut_index[0]
        index_right = rightcut_index[0]

        leftcut = outer_left.get(index_left)
        rightcut = outer_right.get(index_right)

        leftcut_index_2 = outer_left.cut(p1 - normvector * self.total_amount, p2 - normvector * self.total_amount, inner_lists[0][1])
        rightcut_index_2 = outer_right.cut(p1 - normvector * self.total_amount, p2 - normvector * self.total_amount, inner_lists[-1][1])

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