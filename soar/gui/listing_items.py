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

from qgis.PyQt.QtCore import (
    Qt
)
from qgis.PyQt.QtGui import (
    QCursor,
    QColor
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QSizePolicy
)
from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes
)
from qgis.gui import (
    QgsRubberBand
)
from qgis.utils import iface

from ..core.client import Listing


class ListingItemWidgetBase(QFrame):
    """
    Base class for listing items
    """

    THUMBNAIL_CORNER_RADIUS = 5
    THUMBNAIL_SIZE = 150

    CARD_HEIGHT = THUMBNAIL_SIZE + 2  # +2 for 2x1px border
    CARD_HEIGHT_TALL = THUMBNAIL_SIZE + 170 + 2  # +2 for 2x1px border

    def __init__(self, parent=None):
        super().__init__(parent)
        self.column_count = 1
        self.setStyleSheet(
            """DatasetItemWidgetBase {{
               border: 1px solid #dddddd;
               border-radius: {}px; background: white;
            }}""".format(self.THUMBNAIL_CORNER_RADIUS)
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setLayout(QVBoxLayout())


class EmptyDatasetItemWidget(ListingItemWidgetBase):
    """
    Shows an 'empty' listing item
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.thumbnail = QFrame()
        self.thumbnail.setStyleSheet(
            """background: #e6e6e6; border-radius: {}px""".format(
                self.THUMBNAIL_CORNER_RADIUS
            )
        )
        self.layout().addWidget(self.thumbnail)


class ListingItemWidget(ListingItemWidgetBase):
    """
    Shows details for a listing
    """

    def __init__(self, listing: Listing, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)
        self.listing = listing
        self.raw_thumbnail = None

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.layout().addWidget(self.title_label)

        self.title_label.setText(self.listing.title)

        base_style = self.styleSheet()
        base_style += """
            DatasetItemWidget:hover {
                border: 1px solid rgb(180, 180, 180);
                background: #fcfcfc;
            }
        """
        self.setStyleSheet(base_style)

        if self.listing.geometry:
            self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
            self.footprint.setWidth(2)
            self.footprint.setColor(QColor(255, 0, 0, 200))
            self.footprint.setFillColor(QColor(255, 0, 0, 40))
        else:
            self.footprint = None

        self.setCursor(QCursor(Qt.PointingHandCursor))

    # QWidget interface
    # pylint: disable=missing-function-docstring,unused-argument
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.showDetails()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        if self.footprint is not None:
            self._show_footprint()

    def leaveEvent(self, event):
        if self.footprint is not None:
            self._hide_footprint()

    # pylint: enable=missing-function-docstring,unused-argument

    def show_details(self):
        """
        Shows details of the listing
        """

    def extent_in_map_crs(self) -> QgsGeometry:
        """
        Gets the listing's extent in the map canvas CRS
        """
        geom = QgsGeometry(self.listing.geometry)
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            iface.mapCanvas().mapSettings().destinationCrs(),
            QgsProject.instance(),
        )
        geom.transform(transform)
        return geom

    def _show_footprint(self):
        """
        Shows the listing's footprint
        """
        self.footprint.setToGeometry(self.extent_in_map_crs())

    def _hide_footprint(self):
        """
        Hides the listing's footprint
        """
        self.footprint.reset(QgsWkbTypes.PolygonGeometry)
