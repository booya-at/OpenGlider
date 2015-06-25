import collections

from openglider.airfoil import get_x_value
from openglider.plots import sewing_config, PlotPart


def get_ribs(glider):
    ribs = collections.OrderedDict()
    xvalues = glider.profile_x_values

    for i, rib in enumerate(glider.ribs[glider.has_center_cell:-1]):
        rib_no = i + glider.has_center_cell
        chord = rib.chord

        profile = rib.profile_2d.copy()
        profile.scale(chord)

        profile_outer = profile.copy()
        profile_outer.add_stuff(0.01)

        def return_points(x_value):
            """Return points for sewing marks"""
            ik = get_x_value(xvalues, x_value)
            return profile[ik], profile_outer[ik]

        rib_marks = []

        ############# wieder ein kommentieren

        # marks for attachment-points
        attachment_points = filter(lambda p: p.rib == rib, glider.attachment_points)
        for point in attachment_points:
            rib_marks += sewing_config["marks"]["attachment-point"](*return_points(point.rib_pos))

        # marks for panel-cuts
        rib_cuts = set()
        if rib_no > 0:
            for panel in glider.cells[rib_no - 1].panels:
                rib_cuts.add(panel.cut_front["right"])  # left cell
                rib_cuts.add(panel.cut_back["right"])
        for panel in glider.cells[rib_no].panels:
            rib_cuts.add(panel.cut_front["left"])
            rib_cuts.add(panel.cut_back["left"])
        rib_cuts.remove(1)
        rib_cuts.remove(-1)
        for cut in rib_cuts:
            rib_marks += sewing_config["marks"]["panel-cut"](*return_points(cut))

        # general marks

        # holes
        cuts = [profile_outer]
        for hole in rib.holes:
            cuts.append(hole.get_flattened(rib))

        # drib cuts


        #add text, entry, holes

        try:
            profile_outer.close()
        except:
            raise LookupError("ahah {}/{}".format(i, rib.profile_2d))
        ribs[rib] = PlotPart({"CUTS": cuts,
                              "MARKS": [profile] + rib_marks},
                             name="Rib{}".format(rib_no))

    return ribs