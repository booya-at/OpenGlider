from openglider.mesh import Mesh


class MeshGroup(object):
    def __init__(self, *objects):
        self.objects = list(objects)

    def __repr__(self):
        text = "MeshGroup: [\n"
        for obj in self.objects:
            text += "\t{},\n".format(obj)
        text += "]"
        return text

    def __iadd__(self, other):
        assert isinstance(other, MeshGroup)
        self.objects += other.objects
        return self

    def append(self, obj):
        self.objects.append(obj)

    def group_materials(self, join=False):
        by_material = {}
        for obj in self.objects:
            by_material.setdefault(obj.name, self.__class__())
            by_material[obj.name].append(obj)

        if join:
            for key, group in by_material.items():
                by_material[key] = group.join()

        return by_material

    def join(self):
        mesh = Mesh()
        for obj in self.objects:
            mesh += obj
        return mesh

    def export_obj(self, filepath=None):
        offset = 0
        out = ""
        for obj in self.objects:
            out += obj.export_obj(offset=offset)
            offset += len(obj.vertices)

        if filepath is not None:
            with open(filepath, "w") as outfile:
                outfile.write(out)

        return out
