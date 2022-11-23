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

import json
import platform
from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QPointF,
    QRect,
    QRectF,
    QSize
)
from qgis.PyQt.QtGui import (
    QColor,
    QPixmap,
    QCursor,
    QPainter,
    QPainterPath,
    QImage,
    QBrush,
    QFont,
    QPen
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
    QgsFields,
    QgsJsonUtils
)
from qgis.utils import iface

from .gui_utils import GuiUtils
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

        font_scale = self.screen().logicalDotsPerInch() / 92

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.layout().addWidget(self.title_label)

        main_title_size = 11
        if platform.system() == 'Darwin':
            # fonts looks smaller on a mac, where things "just work" :P
            main_title_size = 14
        elif font_scale > 1:
            main_title_size = int(12 / font_scale)

        self.title_label.setText(self.listing.title)

        base_style = self.styleSheet()
        base_style += """
            DatasetItemWidget:hover {
                border: 1px solid rgb(180, 180, 180);
                background: #fcfcfc;
            }
        """
        self.setStyleSheet(base_style)

        #        self.bbox: Optional[QgsGeometry] = self._geomFromGeoJson(
        #           self.dataset.get("data", {}).get("extent"))
        # if self.bbox:
        #     self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        #     self.footprint.setWidth(2)
        #     self.footprint.setColor(QColor(255, 0, 0, 200))
        #     self.footprint.setFillColor(QColor(255, 0, 0, 40))
        # else:
        #     self.footprint = None

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def setThumbnail(self, img: Optional[QImage]):
        self.raw_thumbnail = img
        self.update_thumbnail()

    def update_thumbnail(self):
        thumbnail = self.process_thumbnail(self.raw_thumbnail)
        dpi_ratio = self.screen().devicePixelRatio()
        width = int(thumbnail.width() / dpi_ratio)
        height = int(thumbnail.height() / dpi_ratio)
        self.thumbnail_label.setFixedSize(QSize(width, height))
        self.thumbnail_label.setPixmap(QPixmap.fromImage(thumbnail))

    def process_thumbnail(self, img: Optional[QImage]) -> QImage:
        if self.column_count == 1:
            # sizes here account for borders, hence height is + 2
            size = QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE + 2)
        else:
            size = QSize(self.width(), self.THUMBNAIL_SIZE)

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
        if self.column_count == 1:
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
        else:
            path.moveTo(self.THUMBNAIL_CORNER_RADIUS, 0)
            path.lineTo(size.width() - self.THUMBNAIL_CORNER_RADIUS, 0)
            path.arcTo(size.width() - self.THUMBNAIL_CORNER_RADIUS * 2,
                       0,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       90, -90
                       )
            path.lineTo(size.width(), size.height())
            path.lineTo(0, size.height())
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

        painter = QPainter(base)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRoundedRect(QRectF(15, 100, 117, 32), 4, 4)

        icon = DatasetGuiUtils.get_icon_for_dataset(self.dataset, IconStyle.Light)
        if icon:
            painter.drawImage(QRectF(21, 106, 20, 20),
                              GuiUtils.get_svg_as_image(icon,
                                                        int(20 * scale_factor),
                                                        int(20 * scale_factor)))

        description = DatasetGuiUtils.get_type_description(self.dataset)

        font_scale = self.screen().logicalDotsPerInch() / 92

        overlay_font_size = 7.5
        if platform.system() == 'Darwin':
            overlay_font_size = 9
        elif font_scale > 1:
            overlay_font_size = 7.5 / font_scale

        if description:
            font = QFont('Arial')
            font.setPointSizeF(overlay_font_size / scale_factor)
            font.setBold(True)
            painter.setFont(font)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QPointF(47, 112), description)

        subtitle = DatasetGuiUtils.get_subtitle(self.dataset)
        if subtitle:
            font = QFont('Arial')
            font.setPointSizeF(overlay_font_size / scale_factor)
            font.setBold(False)
            painter.setFont(font)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QPointF(47, 126), subtitle)

        painter.end()
        return base

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.column_count > 1:
            self.update_thumbnail()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.showDetails()
        else:
            super().mousePressEvent(event)

    def showDetails(self):
        dataset = (
            self.dataset
        )
        dlg = DatasetDialog(self, dataset)
        dlg.exec()

    def _geomFromGeoJson(self, geojson) -> Optional[QgsGeometry]:
        try:
            feats = QgsJsonUtils.stringToFeatureList(
                json.dumps(geojson), QgsFields(), None
            )
            geom = feats[0].geometry()
        except Exception:
            geom = QgsGeometry()

        if geom.isNull() or geom.isEmpty():
            return None

        return geom

    # def enterEvent(self, event):
    #     if self.footprint is not None:
    #         self.showFootprint()

    # def leaveEvent(self, event):
    #     if self.footprint is not None:
    #         self.hideFootprint()

    def _bboxInProjectCrs(self):
        geom = QgsGeometry(self.bbox)
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsProject.instance().crs(),
            QgsProject.instance(),
        )
        geom.transform(transform)
        return geom

    # def showFootprint(self):
    #     self.footprint.setToGeometry(self._bboxInProjectCrs())

    # def hideFootprint(self):
    #     self.footprint.reset(QgsWkbTypes.PolygonGeometry)

    def zoomToBoundingBox(self):
        rect = self.bbox.boundingBox()
        rect.scale(1.05)
        iface.mapCanvas().setExtent(rect)
        iface.mapCanvas().refresh()
