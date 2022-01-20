from typing import List, Dict

import euklid

from openglider.vector.drawing.part import PlotPart

text_vectors: Dict[str, List[List[float]]] = {
    "1": [[0.2, 0.5], [0.6, 1.], [0.6, 0.]],
    "2": [[0.2, 1.], [0.8, 1.], [0.8, 0.5], [0.2, 0.5], [0.2, 0.], [0.8, 0.]],
    "3": [[0.2, 1.], [0.8, 1.], [0.8, 0.5], [0.2, 0.5], [0.8, 0.5], [0.8, 0.], [0.2, 0.]],
    "4": [[0.8, 0.5], [0.2, 0.5], [0.6, 1.], [0.6, 0.]],
    "5": [[0.8, 1.], [0.2, 1.], [0.2, 0.5], [0.8, 0.5], [0.8, 0.], [0.2, 0.]],
    "6": [[0.8, 1.], [0.2, 1.], [0.2, 0.5], [0.8, 0.5], [0.8, 0.], [0.2, 0.], [0.2, 0.5]],
    "7": [[0.2, 1.], [0.8, 1.], [0.4, 0.]],
    "8": [[0.8, 0.5], [0.8, 1.], [0.2, 1.], [0.2, 0.5], [0.8, 0.5], [0.8, 0.], [0.2, 0.], [0.2, 0.5]],
    "9": [[0.8, 0.5], [0.2, 0.5], [0.2, 1.], [0.8, 1.], [0.8, 0.], [0.2, 0.]],
    "0": [[0.2, 0.], [0.2, 1.], [0.8, 1.], [0.8, 0.], [0.2, 0.]],
    "A": [[0.1, 0], [0.5, 1.], [0.9, 0], [0.7, 0.5], [0.3, 0.5]],
    "B": [[0.2, 1.], [0.2, 0], [0.7, 0], [0.8, 0.1], [0.8, 0.4], [0.7, 0.5], [0.2, 0.5], [0.7, 0.5], [0.8, 0.6],
          [0.8, 0.9], [0.7, 1.], [0.2, 1.]],
    "C": [[0.8, 1.], [0.3, 1.], [0.2, 0.9], [0.2, 0.1], [0.3, 0], [0.8, 0]],
    "D": [[0.2, 1.], [0.5, 1.], [0.7, 0.9], [0.8, 0.8], [0.9, 0.6], [0.9, 0.4], [0.8, 0.2], [0.7, 0.1], [0.5, 0],
          [0.2, 0], [0.2, 1.]],
    "E": [[0.8, 1.], [0.2, 1.], [0.2, 0.5], [0.8, 0.5], [0.2, 0.5], [0.2, 0], [0.8, 0]],
    "F": [[0.8, 1.], [0.2, 1.], [0.2, 0.5], [0.7, 0.5], [0.2, 0.5], [0.2, 0]],
    "G": [[0.8, 1.], [0.3, 1.], [0.2, 0.9], [0.2, 0.1], [0.3, 0], [0.7, 0], [0.8, 0.1], [0.8, 0.4], [0.7, 0.5],
          [0.5, 0.5]],
    "H": [[0.2, 1.], [0.2, 0], [0.2, 0.5], [0.8, 0.5], [0.8, 0], [0.8, 1.]],
    "I": [[0.4, 1.], [0.6, 1.], [0.5, 1.], [0.5, 0], [0.4, 0], [0.7, 0]],
    "J": [[0.3, 1.], [0.6, 1.], [0.6, 0.1], [0.5, 0], [0.4, 0.1], [0.4, 0.2]],
    "K": [[0.2, 1.], [0.2, 0], [0.2, 0.5], [0.8, 1.], [0.2, 0.5], [0.8, 0]],
    "L": [[0.2, 1.], [0.2, 0], [0.8, 0]],
    "M": [[0.2, 0], [0.2, 1.], [0.5, 0.5], [0.8, 1.], [0.8, 0]],
    "N": [[0.2, 0], [0.2, 1.], [0.8, 0], [0.8, 1.]],
    "O": [[0.2, 0.9], [0.2, 0.1], [0.3, 0.], [0.7, 0.], [0.8, 0.1], [0.8, 0.9], [0.7, 1.], [0.3, 1.], [0.2, 0.9]],
    "P": [[0.2, 0.], [0.2, 0.9], [0.3, 1.], [0.7, 1.], [0.8, 0.9], [0.8, 0.6], [0.7, 0.5], [0.2, 0.5]],
    "Q": [[0.2, 0.9], [0.3, 1.], [0.8, 1.], [0.9, 0.9], [0.9, 0.1], [0.8, 0.], [0.9, 0], [0.3, 0], [0.2, 0.1],
          [0.2, 0.9]],
    "R": [[0.2, 0.], [0.2, 0.9], [0.3, 1.], [0.7, 1.], [0.8, 0.9], [0.8, 0.6], [0.7, 0.5], [0.2, 0.5], [0.8, 0.]],
    "S": [[0.8, 0.9], [0.7, 1.], [0.3, 1.], [0.2, 0.9], [0.2, 0.6], [0.3, 0.5], [0.7, 0.5], [0.8, 0.4], [0.8, 0.1],
          [0.7, 0], [0.3, 0], [0.2, 0.1]],
    "T": [[0.2, 1.], [0.8, 1.], [0.5, 1.], [0.5, 0]],
    "U": [[0.2, 1.], [0.2, 0.1], [0.3, 0], [0.7, 0], [0.8, 0.1], [0.8, 1.]],
    "V": [[0.2, 1.], [0.5, 0], [0.8, 1.]],
    "W": [[0.2, 1.], [0.3, 0], [0.5, 0.5], [0.7, 0], [0.8, 1.]],
    "X": [[0.2, 1.], [0.8, 0], [0.5, 0.5], [0.8, 1.], [0.2, 0]],
    "Y": [[0.2, 1.], [0.2, 0.6], [0.3, 0.5], [0.7, 0.5], [0.8, 0.6], [0.8, 1.], [0.8, 0.6], [0.7, 0.5], [0.8, 0.4],
          [0.8, 0.1], [0.7, 0]],
    "Z": [[0.2, 1.], [0.8, 1.], [0.2, 0], [0.8, 0]],
    "_": [[0.2, 0.], [0.8, 0.]],
    "-": [[0.2, 0.5], [0.8, 0.5]],
    " ": [],
    ".": [[0.48, 0], [0.52, 0], [0.52, 0.04], [0.48, 0.04], [0.48, 0]]
}


class Text(object):
    letters = text_vectors
    def __init__(self, text, p1, p2, size=None, align="left", height=0.8, space=0.2, valign=0.5):
        """
        Vector Text
        :param text: Text
        :param p1: left orientation point
        :param p2: right orientation point
        :param size: letter size. if not set, letters are fit into space (p1/p2)
        :param align: horizontal align: ("left", "right", "center")
        :param height: letter height, relative to width
        :param space: space in between letters
        :param valign: vertical align ( -0.5: bottom, 0: centered, 0.5: top)
        """
        self.text = text
        self.p1 = euklid.vector.Vector2D(list(p1)[:])
        self.p2 = euklid.vector.Vector2D(list(p2)[:])
        self.size = size
        self.height = height
        self.space = space
        self.align = align
        self.valign = valign

    def __json__(self):
        return {
            "text": self.text,
            "p1": self.p1,
            "p2": self.p2,
            "size": self.size,
            "height": self.height,
            "space": self.space,
            "align": self.align
        }

    def get_letter(self, letter, replace_unknown=True) -> List[List[List[float]]]:
        letter = letter.upper()
        if letter not in self.letters:
                if replace_unknown:
                    letter = "_"
                else:
                    raise KeyError("Letter {} from word '{}' not available".format(letter, self.text.upper()))
        
        letter_vec = self.letters[letter]
        
        return [letter_vec]

    def get_vectors(self, replace_unknown=True) -> List[euklid.vector.PolyLine2D]:
        # todo: add valign (space)
        vectors = []
        diff = self.p2 - self.p1

        letter_width = self.size
        if letter_width is None:
            letter_width = diff.length() / len(self.text)

        letter_height = self.height * letter_width
        angle = diff.angle()

        text_width = len(self.text) * letter_width

        if self.align == "left":
            p1 = self.p1.copy()
        elif self.align == "center":
            p1 = self.p1 + diff * 0.5 - diff.normalized() * (text_width/2)
        elif self.align == "right":
            p1 = self.p2 - diff.normalized() * text_width
        else:
            raise ValueError(f"invalid alignment: {self.align}")


        letter_pos = euklid.vector.Vector2D([0, letter_height * (self.valign - 0.5)])

        for letter in self.text:
            points = self.get_letter(letter, replace_unknown=replace_unknown)
            for lst in points:
                if lst:
                    line = euklid.vector.PolyLine2D(lst)\
                        .scale(euklid.vector.Vector2D([letter_width, letter_height]))\
                        .move(letter_pos)\
                        .rotate(angle, euklid.vector.Vector2D([0, 0]))\
                        .move(p1)

                    vectors.append(line)

            letter_pos += euklid.vector.Vector2D([letter_width, 0])

        return vectors

    def get_plotpart(self, replace_unknown=True) -> PlotPart:
        vectors = self.get_vectors(replace_unknown)
        return PlotPart(vectors)
