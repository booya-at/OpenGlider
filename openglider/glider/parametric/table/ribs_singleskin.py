from typing import Dict, Optional

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable

import logging

logger = logging.getLogger(__name__)

class SingleSkinTable(ElementTable):
    keywords = [
        ("SkinRib", 2),  # continued_min_end, xrot
    ]

    def get_element(self, keyword, data) -> Dict[str, float]:
        return {
            "continued_min_end": data[0],
            "xrot": data[1]
        }