from openglider.lines.line_types.linetype import LineType

def A8001(strength: int, diameter: float, weight: float) -> None:
    LineType(
        f"edelrid.A-8001-{strength:03d}",
        diameter,
        [[10*strength, 0.05]],
        10*strength,
        weight,
        sheated=False,
        colors=["orange", "blue", "magenta", ]
        )


A8001(25, 0.4, 0.15)
A8001(50, 0.5, 0.25)
A8001(70, 0.7, 0.4)
A8001(90, 0.8, 0.55)
A8001(130, 1.0, 0.8)
A8001(135, 1.1, 0.85)
A8001(190, 1.2, 1.1)
A8001(230, 1.5, 1.4)
A8001(280, 1.7, 1.7)
A8001(340, 1.9, 2.1)
A8001(470, 2.2, 2.8)
