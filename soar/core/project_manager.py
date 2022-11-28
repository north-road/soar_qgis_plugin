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

from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    QDateTime,
    QObject
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.core import (
    QgsProject,
    QgsNetworkAccessManager,
    QgsMapLayer
)

from .client import ApiClient


class ProjectManager(QObject):
    """
    Responsible for watching projects and updating layers from projects as required
    """

    def __init__(self, project: QgsProject, parent=None):
        super().__init__(parent)
        self.project = project

        self.project.layerWasAdded.connect(self._on_layer_added)

        self.api_client = ApiClient()

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

        request = self.api_client.request_listing(soar_layer_id)
        reply = QgsNetworkAccessManager.instance().get(request)
        reply.finished.connect(partial(self._listing_fetched, reply, layer))

    def _listing_fetched(self, reply: QNetworkReply, layer: QgsMapLayer):
        """
        Called when a listing has been fetched and we are ready to update a layer's URI
        """
        full_listing = self.api_client.parse_listing_reply(reply)

        new_uri = full_listing.to_qgis_layer_source_string()
        layer.setDataSource(new_uri, layer.name(), 'wms')

        layer.setCustomProperty('_soar_layer_expiry',
                                full_listing.tile_url_expiry_at.toString(Qt.ISODate))
