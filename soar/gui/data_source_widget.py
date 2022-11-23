# -*- coding: utf-8 -*-
"""soar.earth plugin

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

from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
)
from qgis.gui import (
    QgsAbstractDataSourceWidget
)

from .browse_widget import BrowseWidget


class SoarDataSourceWidget(QgsAbstractDataSourceWidget):
    """
    QGIS Data source manager widget for browsing soar.earth data
    """

    def __init__(self):
        super().__init__()

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        self.browse_widget = BrowseWidget()

        vl.addWidget(self.browse_widget)
        self.setLayout(vl)
