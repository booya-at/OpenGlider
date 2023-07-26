from .aoa import AOAWizard
from .arc import ArcWidget
from .ballooning import BallooningWidget
from .curves import CurveWizard
from .distribution import BallooningCurveWizard, ProfileDistributionWizzard
from .shape import ShapeWizard

input_wizzards = [
    (BallooningWidget, "Ballooning"),
    (BallooningCurveWizard, "BallooningCurve"),
    (ProfileDistributionWizzard, "ProfileCurve"),
    (ArcWidget, "Arc"),
    (ShapeWizard, "Shape"),
    (CurveWizard, "Curve"),
    (AOAWizard, "AOA")
]