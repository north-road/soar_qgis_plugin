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
    QSize,
    QRect,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QCursor,
    QColor,
    QImage,
    QPixmap,
    QPainter,
    QBrush,
    QPainterPath
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
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

from .thumbnail_manager import download_thumbnail
from ..core.client import Listing


class ListingItemWidgetBase(QFrame):
    """
    Base class for listing items
    """

    THUMBNAIL_CORNER_RADIUS = 5
    THUMBNAIL_SIZE = 100

    CARD_HEIGHT = THUMBNAIL_SIZE + 2  # +2 for 2x1px border

    def __init__(self, parent=None):
        super().__init__(parent)
        self.column_count = 1
        self.setStyleSheet(
            """ListingItemWidgetBase {{
               border: 1px solid #dddddd;
               border-radius: {}px; background: white;
            }}""".format(self.THUMBNAIL_CORNER_RADIUS)
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setMinimumWidth(self.CARD_HEIGHT * 3)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


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


class ThumbnailWidget(QLabel):
    """
    Widget for displaying thumbnail images
    """

    def __init__(self):
        super().__init__()
        self.setMaximumSize(100, 100)
        self.setMinimumSize(100, 100)


class ListingItemWidget(ListingItemWidgetBase):
    """
    Shows details for a listing
    """

    clicked = pyqtSignal(Listing)

    def __init__(self, listing: Listing, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)
        self.listing = listing

        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)

        self.thumbnail_widget = ThumbnailWidget()
        self.thumbnail_widget.setFixedSize(100, 100)

        hl.addWidget(self.thumbnail_widget)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        if listing.preview_url:
            download_thumbnail(listing.preview_url, self)

        hl.addWidget(self.title_label, 1)
        self.layout().addLayout(hl)

        self.title_label.setText(self.listing.title)

        base_style = self.styleSheet()
        base_style += """
            ListingItemWidget:hover {
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
            self.clicked.emit(self.listing)
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        if self.footprint is not None:
            self._show_footprint()

    def leaveEvent(self, event):
        if self.footprint is not None:
            self._hide_footprint()

    # pylint: enable=missing-function-docstring,unused-argument

    def set_thumbnail(self, img: Optional[QImage]):
        """
        Sets the item thumbnail
        """
        thumbnail = self.process_thumbnail(img)

        dpi_ratio = self.screen().devicePixelRatio()
        width = int(thumbnail.width() / dpi_ratio)
        height = int(thumbnail.height() / dpi_ratio)

        self.thumbnail_widget.setFixedSize(QSize(width, height))
        self.thumbnail_widget.setPixmap(QPixmap.fromImage(thumbnail))

    def process_thumbnail(self, img: Optional[QImage]) -> QImage:
        """
        Processes a listing's thumbnail for pretty display
        """
        # sizes here account for borders, hence height is + 2
        size = QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE + 2)

        image_size = size
        scale_factor = self.screen().devicePixelRatio()
        if scale_factor > 1:
            image_size *= scale_factor

        target = QImage(image_size, QImage.Format_ARGB32)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))

        path = QPainterPath()
        path.moveTo(self.THUMBNAIL_CORNER_RADIUS, 0)
        path.lineTo(size.width(), 0)
        path.lineTo(size.width(), size.height())
        path.lineTo(self.THUMBNAIL_CORNER_RADIUS, size.height())
        path.arcTo(0,
                   size.height() - self.THUMBNAIL_CORNER_RADIUS * 2,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   270, -90
                   )
        path.lineTo(0, self.THUMBNAIL_CORNER_RADIUS)
        path.arcTo(0,
                   0,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   self.THUMBNAIL_CORNER_RADIUS * 2,
                   180, -90
                   )

        painter.drawPath(path)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)

        if img is not None:
            resized = img.scaled(image_size.width(),
                                 image_size.height(),
                                 Qt.KeepAspectRatioByExpanding,
                                 Qt.SmoothTransformation)
            if resized.width() > image_size.width():
                left = int((resized.width() - image_size.width()) / 2)
            else:
                left = 0
            if resized.height() > image_size.height():
                top = int((resized.height() - image_size.height()) / 2)
            else:
                top = 0

            cropped = resized.copy(QRect(left, top, image_size.width(), image_size.height()))
            painter.drawImage(0, 0, cropped)
        else:
            painter.setBrush(QBrush(QColor('#cccccc')))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 600, 600)
        painter.end()

        target.setDevicePixelRatio(scale_factor)
        target.setDotsPerMeterX(
            int(target.dotsPerMeterX() * scale_factor))
        target.setDotsPerMeterY(int(
            target.dotsPerMeterY() * scale_factor))
        base = target

        return base

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
