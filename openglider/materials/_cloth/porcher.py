from openglider.materials.material import Material


class Porcher(Material):
    manufacturer = "porcher"


class Skytex32(Porcher):
    weight = 32
    name="skytex_32"


materials = [
    Porcher(name="skytex_32_hf", weight=32),
    Skytex32(color="white", color_code="FFFFFF"),
    Skytex32(color="purple", color_code="8F4795"),
    Skytex32(color="electric_blue", color_code="4F81BD"),
    Skytex32(color="royal_blue", color_code="0F81C4"),
    Skytex32(color="petrol_blue", color_code="01567D"),
    Skytex32(color="deep_blue", color_code="243882"),
    Skytex32(color="lime_green_500", color_code="96C11E"),
    Skytex32(color="lime_green_530", color_code="BCB21F"),
    Skytex32(color="green_551", color_code="9BBB59"),
    Skytex32(color="dragon_red", color_code="E62E39"),
    Skytex32(color="sangria", color_code="AE2760"),
    Skytex32(color="orange", color_code="EC6728"),
    Skytex32(color="lemon", color_code="C4D79B"),
    Skytex32(color="gold", color_code="FBBD3D"),
    Skytex32(color="dark_red", color_code="8C1C40"),
    Skytex32(color="sunflower", color_code="FDC529"),
    Skytex32(color="black", color_code="000000"),
]

class Skytex38(Porcher):
    weight = 38
    name = "skytex_38"

materials += [
    Porcher(name="skytex_38_hf", weight=38),
    Skytex38(color="black", color_code="000000"),
    Skytex38(color="white", color_code="FFFFFF"),
    Skytex38(color="dark_grey", color_code="909C9C"),
    Skytex38(color="lime_green_500", color_code="96C11E"),
    Skytex38(color="lime_green_530", color_code="BCB21F"),
    Skytex38(color="green", color_code="00945E"),
    Skytex38(color="sunflower", color_code="FDC529"),
    Skytex38(color="gold", color_code="FBBD3D"),
    Skytex38(color="orange", color_code="EC6728"),
    Skytex38(color="dragon_red", color_code="E62E39"),
    Skytex38(color="dark_red", color_code="8C1C40"),
    Skytex38(color="sangria", color_code="AE2760"),
    Skytex38(color="purple", color_code="8F4795"),
    Skytex38(color="royal_blue", color_code="0F81C4"),
    Skytex38(color="petrol_blue", color_code="01567D"),
    Skytex38(color="deep_blue", color_code="243882"),
]

class Skytex27(Porcher):
    weight = 27
    name = "skytex_27"

class Skytex27DC(Porcher):
    weight = 29
    name = "skytex_27_dc"

materials += [
    Skytex27(color="white", color_code="FFFFFF"),
    Skytex27DC(color="white", color_code="FFFFFF"),
    Skytex27DC(color="dragon_red", color_code="E62E39"),
    Skytex27DC(color="petrol_blue", color_code="01567D")
]
