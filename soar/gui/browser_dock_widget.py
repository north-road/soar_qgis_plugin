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
    QWidget
)
from qgis.gui import (
    QgsDockWidget
)

from .browse_widget import BrowseWidget


class BrowserDockWidget(QgsDockWidget):
    """
    A dock widget for browsing soar.earth listings
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('SoarBrowserDockWidget')
        self.setWindowTitle(self.tr('Soar.earth Browser'))

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        self.browser = BrowseWidget()
        vl.addWidget(self.browser)

        w = QWidget()
        w.setLayout(vl)
        self.setWidget(w)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        self.browser.cancel_active_requests()
