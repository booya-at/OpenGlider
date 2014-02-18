import openglider.Vector


###############CUTS####################
# Check doc/drawings 7-9 for sketches
# DESIGN-CUT Style
def cut_1(inner_lists, outer_left, outer_right, amount):
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))

    newlist = []
    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])  # p1,p2,startpoint
    newlist.append(leftcut[0])
    newlist.append(leftcut[0]+normvector*amount)
    for thislist in inner_lists:
        newlist.append(thislist[0][thislist[1]] + normvector*amount)
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])
    newlist.append(rightcut[0]+normvector*amount)
    newlist.append(rightcut[0])

    return newlist, leftcut[1], rightcut[1]


# OPEN-ENTRY Style
def cut_2(inner_lists, outer_left, outer_right, amount):
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))

    newlist = []
    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])

    leftcut_2 = outer_left.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1])
    rightcut_2 = outer_right.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1])

    piece1 = outer_left[leftcut[1]:leftcut_2[1]]
    piece2 = outer_right[rightcut[1]:rightcut_2[1]]

    # mirror to (p1-p2) -> p'=p-2*(p.normvector)

    for point in piece1[::]:
        newlist.append(point - 2*normvector*normvector.dot(point-leftcut[0]))
    last = newlist[-1]
    for point in piece1[::-1]:
        newlist.append(-(leftcut_2[0] - point) + last)

    cuts2 = []
    for point in piece2[::]:
        cuts2.append(point - 2*normvector*normvector.dot(point-rightcut[0]))
    last = cuts2[-1]
    for point in piece2[::-1]:
        cuts2.append(-(rightcut_2[0] - point) + last)

    return newlist+cuts2[::-1], leftcut[1], rightcut[1]


# TRAILING-EDGE Style
def cut_3(inner_lists, outer_left, outer_right, amount):
    # Continue Parallel
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))

    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])

    leftcut_2 = outer_left.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1])
    rightcut_2 = outer_right.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1])
    diff = (leftcut[0]-leftcut_2[0] + rightcut[0] - rightcut_2[0])/2

    newlist = [leftcut[0], leftcut[0]+diff, rightcut[0]+diff, rightcut[0]]

    return newlist, leftcut[1], rightcut[1]

cuts = [cut_1, cut_2, cut_3]