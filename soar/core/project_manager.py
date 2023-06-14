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

from functools import partial
from typing import List, Optional

from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    QDateTime,
    QObject,
    QSize
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.core import (
    QgsProject,
    QgsNetworkAccessManager,
    QgsMapLayer,
    QgsRectangle
)

from .client import API_CLIENT


class ProjectManager(QObject):
    """
    Responsible for watching projects and updating layers from projects as required
    """

    def __init__(self, project: QgsProject, parent=None):
        super().__init__(parent)
        self.project = project

        self.project.layerWasAdded.connect(self._on_layer_added)

    def _on_layer_added(self, layer: QgsMapLayer):
        """
        Called whenever a new layer is added to the project (or for each layer when the user
        opens an existing project)
        """

        # we defer this by a second, as we don't want this logic happening right on project load!
        _update_timeout = QTimer(self)
        _update_timeout.setSingleShot(True)
        _update_timeout.timeout.connect(partial(self._check_layer_uri, layer))
        _update_timeout.timeout.connect(_update_timeout.deleteLater)
        _update_timeout.setInterval(1000)
        _update_timeout.start()

    def _check_layer_uri(self, layer: QgsMapLayer):
        """
        Checks whether we need to refresh a layer's URI
        """
        soar_layer_id = layer.customProperty('_soar_layer_id')
        if not soar_layer_id:
            return  # don't care about this layer

        # restore real layer extent
        x_min = layer.customProperty('_real_extent_x_min')
        y_min = layer.customProperty('_real_extent_y_min')
        x_max = layer.customProperty('_real_extent_x_max')
        y_max = layer.customProperty('_real_extent_y_max')
        if x_min is not None:
            layer.setExtent(QgsRectangle(x_min, y_min, x_max, y_max))

        soar_layer_expiry = QDateTime.fromString(layer.customProperty('_soar_layer_expiry'),
                                                 Qt.ISODate)
        remaining_days = QDateTime.currentDateTime().daysTo(soar_layer_expiry)

        if remaining_days > 2:
            # still some time remaining, leave layer url unchanged
            return

        self._refresh_layer_uri(layer)

    def _refresh_layer_uri(self, layer):
        """
        Triggers a refresh of a layer's URI
        """
        soar_layer_id = layer.customProperty('_soar_layer_id')

        request = API_CLIENT.request_listing(soar_layer_id)
        reply = QgsNetworkAccessManager.instance().get(request)
        reply.finished.connect(partial(self._listing_fetched, reply, layer))

    def _listing_fetched(self, reply: QNetworkReply, layer: QgsMapLayer):
        """
        Called when a listing has been fetched and we are ready to update a layer's URI
        """
        full_listing = API_CLIENT.parse_listing_reply(reply)

        new_uri = full_listing.to_qgis_layer_source_string()
        # we've overridden the layer's extent from its default
        # This will be reset on the call to setDataSource, so we need to restore
        # the existing extent
        old_extent = layer.extent()
        layer.setDataSource(new_uri, layer.name(), 'wms')
        layer.setExtent(old_extent)

        layer.setCustomProperty('_soar_layer_expiry',
                                full_listing.tile_url_expiry_at.toString(Qt.ISODate))

    def soar_map_title(self) -> str:
        """
        Returns the map title to use when exporting the project to soar.earth
        """
        title, _ = self.project.readEntry('soar', 'map_title')
        if title:
            return title

        return self.project.metadata().title()

    def set_soar_map_title(self, title: str):
        """
        Sets the map title to use when exporting the project to soar.earth
        """
        if title == self.soar_map_title():
            return

        self.project.writeEntry('soar', 'map_title', title)
        self.project.setDirty(True)

    def soar_map_description(self) -> str:
        """
        Returns the map description to use when exporting the project to soar.earth
        """
        description, _ = self.project.readEntry('soar', 'map_description')
        if description:
            return description

        return self.project.metadata().abstract()

    def set_soar_map_description(self, description: str):
        """
        Sets the map description to use when exporting the project to soar.earth
        """
        if description == self.soar_map_description():
            return

        self.project.writeEntry('soar', 'map_description', description)
        self.project.setDirty(True)

    def soar_map_tags(self) -> List[str]:
        """
        Returns the map tags to use when exporting the project to soar.earth
        """
        tags, _ = self.project.readListEntry('soar', 'map_tags')
        if tags:
            return tags

        tags = set()
        keywords = self.project.metadata().keywords()
        for _, words in keywords.items():
            for word in words:
                tags.add(word)

        return list(tags)

    def set_soar_map_tags(self, tags: List[str]):
        """
        Sets the map tags to use when exporting the project to soar.earth
        """
        if set(tags) == set(self.soar_map_tags()):
            return

        self.project.writeEntry('soar', 'map_tags', tags)
        self.project.setDirty(True)

    def soar_category(self, index: int = 1) -> Optional[str]:
        """
        Returns the soar category for the map
        """
        cat, _ = self.project.readEntry('soar', 'map_category{}'.format(
            str(index) if index > 1 else ''
        )
                                        )
        if cat:
            return cat

        if index > 1:
            return None

        project_metadata_cats = self.project.metadata().categories()
        # map from qgis (ISO) categories to soar
        category_map = {
            'Biota': 'climate',
            'Boundaries': 'political',
            'Climatology Meteorology Atmosphere': 'climate',
            'Economy': 'economic',
            'Environment': 'climate',
            'Farming': 'agriculture',
            'Geoscientific Information': 'geology',
            'Health': 'political',
            'Imagery Base Maps Earth Cover': 'earth-art',
            'Inland Waters': 'marine',
            'Intelligence Military': 'political',
            'Location': 'political',
            'Oceans': 'marine',
            'Planning Cadastre': 'political',
            'Society': 'political',
            'Structure': 'urban',
            'Transportation': 'transport',
            'Utilities Communication': 'urban'
        }
        for iso_cat, soar_cat in category_map.items():
            if iso_cat in project_metadata_cats:
                return soar_cat

        return None

    def set_soar_category(self, category: str, index: int = 1):
        """
        Sets the map category to use when exporting the project to soar.earth
        """
        if category == self.soar_category(index):
            return

        self.project.writeEntry('soar', 'map_category{}'.format(
            str(index) if index > 1 else ''
        ), category)
        self.project.setDirty(True)

    def export_size(self) -> QSize:
        """
        Returns the stored export size, if set
        """
        width, ok = self.project.readNumEntry('soar', 'export_width')
        if not ok:
            return QSize()

        height, ok = self.project.readNumEntry('soar', 'export_height')
        if not ok:
            return QSize()

        return QSize(width, height)

    def set_export_size(self, size: QSize):
        """
        Sets the size to use for map exports
        """
        if size == self.export_size():
            return

        self.project.writeEntry('soar', 'export_width', size.width())
        self.project.writeEntry('soar', 'export_height', size.height())
        self.project.setDirty(True)

    def export_scale(self) -> Optional[float]:
        """
        Returns the stored export scale, if set
        """
        scale, ok = self.project.readDoubleEntry('soar', 'export_scale')
        if not ok:
            return None
        return scale

    def set_export_scale(self, scale: float):
        """
        Sets the scale to use for map exports
        """
        if scale == self.export_scale():
            return

        self.project.writeEntryDouble('soar', 'export_scale', scale)
        self.project.setDirty(True)

    def export_extent(self) -> Optional[QgsRectangle]:
        """
        Returns the export extent, if set
        """

        x_min, ok = self.project.readDoubleEntry('soar', 'export_x_min')
        if not ok:
            return None

        y_min, ok = self.project.readDoubleEntry('soar', 'export_y_min')
        if not ok:
            return None

        x_max, ok = self.project.readDoubleEntry('soar', 'export_x_max')
        if not ok:
            return None

        y_max, ok = self.project.readDoubleEntry('soar', 'export_y_max')
        if not ok:
            return None

        return QgsRectangle(x_min, y_min, x_max, y_max)

    def set_export_extent(self, extent: QgsRectangle):
        """
        Sets the stored map export extent
        """
        if extent == self.export_extent():
            return

        self.project.writeEntryDouble('soar', 'export_x_min', extent.xMinimum())
        self.project.writeEntryDouble('soar', 'export_y_min', extent.yMinimum())
        self.project.writeEntryDouble('soar', 'export_x_max', extent.xMaximum())
        self.project.writeEntryDouble('soar', 'export_y_max', extent.yMaximum())
        self.project.setDirty(True)
