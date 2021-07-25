from typing import List
import os
import re
import math
import tempfile
import shutil
import logging

import euklid
import pyfoil

from openglider.utils.distribution import Distribution


logger = logging.getLogger(__name__)


class Profile2D(pyfoil.Airfoil):
    pass