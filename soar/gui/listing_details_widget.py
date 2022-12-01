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

from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal,
    QSize
)
from qgis.PyQt.QtGui import (
    QImage,
    QPixmap
)
from qgis.PyQt.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QPushButton
)
from qgis.gui import (
    QgsPanelWidget
)

from ..core.client import (
    Listing
)
from .thumbnail_manager import download_thumbnail

PAGE_SIZE = 20


class ListingDetailsWidget(QgsPanelWidget):
    """
    A widget showing listing details
    """

    add_to_map = pyqtSignal(Listing)

    def __init__(self, listing: Listing, parent=None):
        super().__init__(parent)

        self.listing = listing
        self.setPanelTitle(self.listing.title)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel()
        title_label.setText(f'<h1>{self.listing.title}</h1>')
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        self.thumbnail_widget = QLabel()
        self.thumbnail_widget.setFixedSize(100, 100)
        layout.addWidget(self.thumbnail_widget)

        description_label = QLabel(self.listing.description)
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(description_label, 1)

        add_to_map_button = QPushButton(self.tr('Add to Map'))
        add_to_map_button.clicked.connect(self.add_to_map_clicked)
        layout.addWidget(add_to_map_button)

        if listing.preview_url:
            download_thumbnail(listing.preview_url, self)

        self.setLayout(layout)

    def set_thumbnail(self, img: Optional[QImage]):
        """
        Sets the item thumbnail
        """
        dpi_ratio = self.screen().devicePixelRatio()
        width = int(img.width() / dpi_ratio)
        height = int(img.height() / dpi_ratio)

        self.thumbnail_widget.setFixedSize(QSize(width, height))
        self.thumbnail_widget.setPixmap(QPixmap.fromImage(img))

    def add_to_map_clicked(self):
        """
        Trigged when the user wants to add the listing to the map
        """
        self.add_to_map.emit(self.listing)
