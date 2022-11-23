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
    QWidget,
    QVBoxLayout
)
from qgis.gui import (
    QgsFilterLineEdit
)

from .listings_browser_widget import ListingsBrowserWidget
from ..core.client import ListingQuery


class BrowseWidget(QWidget):
    """
    A widget for browsing listings from soar.earth
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        vl = QVBoxLayout()

        self.search_edit =QgsFilterLineEdit()
        self.search_edit.setShowSearchIcon(True)
        self.search_edit.setShowClearButton(True)
        self.search_edit.setPlaceholderText(self.tr('Search'))
        self.search_edit.textChanged.connect(self._search)

        vl.addWidget(self.search_edit)

        self.browser = ListingsBrowserWidget()
        vl.addWidget(self.browser, 1)

        self.setLayout(vl)

    def _search(self):
        query = ListingQuery(keywords=self.search_edit.text())
        self.browser.populate(query)


