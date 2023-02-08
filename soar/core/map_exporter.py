# -*- coding: utf-8 -*-
"""soar.earth API client

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2022 by Nyall Dawson'
__date__ = '22/11/2022'
__copyright__ = 'Copyright 2022, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from typing import List

from qgis.PyQt.QtCore import (
    QSize
)
from qgis.core import (
    QgsRectangle
)


class MapExportSettings:
    """
    Contains map export/publishing settings
    """

    def __init__(self):
        self.title: str = ''
        self.description: str = ''
        self.tags: List[str] = []
        self.category: str = ''
        self.size: QSize = QSize()
        self.scale: float = 0
        self.extent: QgsRectangle = QgsRectangle()


class MapExporter:
    pass
