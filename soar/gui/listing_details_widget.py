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
    QPixmap,
    QTextDocument,
    QFontMetrics
)
from qgis.PyQt.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QPushButton
)
from qgis.gui import (
    QgsPanelWidget
)

from .thumbnail_manager import download_thumbnail
from ..core.client import (
    Listing
)

PAGE_SIZE = 20


class ListingDetailsWidget(QgsPanelWidget):
    """
    A widget showing listing details
    """

    add_to_map = pyqtSignal(Listing)

    def __init__(self, listing: Listing, parent=None):  # pylint: disable=too-many-statements
        super().__init__(parent)

        self.listing = listing
        self.setPanelTitle(self.listing.title)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel()
        title_label.setText(f'<h1>{self.listing.title}</h1>')
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        credit_label = QLabel()
        credit_label.setText(self.tr('By {}').format(f'<a href="{self.listing.user.permalink()}">{self.listing.user.name}</a>'))
        credit_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        credit_label.setOpenExternalLinks(True)
        credit_label.setWordWrap(True)
        layout.addWidget(credit_label)

        link_label = QLabel()
        link_label.setText(self.tr('View on {}soar.earth{}').format(f'<a href="{self.listing.permalink()}">', '</a>'))
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link_label.setOpenExternalLinks(True)
        link_label.setWordWrap(True)
        layout.addWidget(link_label)

        created_label = QLabel()
        created_label.setText(self.tr('Created: {}').format(self.listing.created_at.toString('yyyy-MM-dd')))
        layout.addWidget(created_label)

        updated_label = QLabel()
        updated_label.setText(self.tr('Updated: {}').format(self.listing.updated_at.toString('yyyy-MM-dd')))
        layout.addWidget(updated_label)

        self.thumbnail_widget = QLabel()
        self.thumbnail_widget.setFixedSize(100, 100)
        layout.addWidget(self.thumbnail_widget)

        try:
            description = QTextDocument()
            description.setMarkdown(self.listing.description)
            description_html = description.toHtml()
        except AttributeError:
            description_html = self.listing.description

        description_label = QLabel(description_html)
        description_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        description_label.setOpenExternalLinks(True)
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(description_label)

        layout.addSpacing(QFontMetrics(self.font()).height() * 2)

        add_to_map_button = QPushButton(self.tr('Add to Map'))
        add_to_map_button.clicked.connect(self.add_to_map_clicked)
        layout.addWidget(add_to_map_button)

        layout.addStretch()

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
