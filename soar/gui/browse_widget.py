# -*- coding: utf-8 -*-
"""Soar plugin

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
from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QTimer
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QComboBox
)
from qgis.core import (
    QgsNetworkAccessManager,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsCsException
)
from qgis.gui import (
    QgsFilterLineEdit,
    QgsPanelWidgetStack
)
from qgis.utils import iface

from .listing_details_widget import ListingDetailsWidget
from .listings_browser_widget import ListingsBrowserWidget
from ..core.client import (
    API_CLIENT,
    Listing,
    ListingType,
    ListingQuery
)


class BrowseWidget(QWidget):
    """
    A widget for browsing listings from soar.earth
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.search_edit = QgsFilterLineEdit()
        self.search_edit.setShowSearchIcon(True)
        self.search_edit.setShowClearButton(True)
        self.search_edit.setPlaceholderText(self.tr('Search'))
        self.search_edit.textChanged.connect(self._filter_widget_changed)

        vl = QVBoxLayout()
        vl.addWidget(self.search_edit)

        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)

        self.category_combo = QComboBox()
        self.category_combo.addItem(self.tr('All Categories'))
        self.category_combo.addItem(self.tr('Agriculture'), 'agriculture')
        self.category_combo.addItem(self.tr('Climate'), 'climate')
        self.category_combo.addItem(self.tr('Earth Art'), 'earth-art')
        self.category_combo.addItem(self.tr('Economic'), 'economic')
        self.category_combo.addItem(self.tr('Geology'), 'geology')
        self.category_combo.addItem(self.tr('History'), 'history')
        self.category_combo.addItem(self.tr('Marine'), 'marine')
        self.category_combo.addItem(self.tr('Political'), 'political')
        self.category_combo.addItem(self.tr('Terrain'), 'terrain')
        self.category_combo.addItem(self.tr('Transport'), 'transport')
        self.category_combo.addItem(self.tr('Urban'), 'urban')

        self.category_combo.currentIndexChanged.connect(self._filter_widget_changed)

        hl.addWidget(self.category_combo, 1)

        self.restrict_to_map_extent = QCheckBox(self.tr('Filter by map extent'))
        self.restrict_to_map_extent.toggled.connect(self._filter_widget_changed)
        hl.addWidget(self.restrict_to_map_extent)

        vl.addLayout(hl)

        self.panel_stack = QgsPanelWidgetStack()

        self.browser = ListingsBrowserWidget()
        self.browser.listing_clicked.connect(self._on_listing_clicked)

        self.panel_stack.setMainPanel(self.browser)

        self.listing_details_pane: Optional[ListingDetailsWidget] = None

        vl.addWidget(self.panel_stack, 1)

        self.setLayout(vl)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        iface.mapCanvas().extentsChanged.connect(self._map_extent_changed)

        self._current_listing_reply: Optional[QNetworkReply] = None

    def _filter_widget_changed(self):
        """
        Triggered whenever any of the search filter widgets are changed
        """
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

    def _map_extent_changed(self):
        """
        Triggered whenever the map canvas extent is changed
        """
        if not self.restrict_to_map_extent.isChecked():
            return

        self._filter_widget_changed()

    def _update_query(self):
        """
        Updates the listings
        """
        query = ListingQuery(keywords=self.search_edit.text())

        category = self.category_combo.currentData()
        if category:
            query.category = category

        if self.restrict_to_map_extent.isChecked():
            target_crs = QgsCoordinateReferenceSystem('EPSG:4326')
            transform = QgsCoordinateTransform(iface.mapCanvas().mapSettings().destinationCrs(),
                                               target_crs,
                                               QgsProject.instance().transformContext())

            visible_polygon = iface.mapCanvas().mapSettings().visiblePolygon()
            # close polygon
            visible_polygon.append(visible_polygon.at(0))
            polygon_map = QgsGeometry.fromQPolygonF(visible_polygon)
            try:
                polygon_map.transform(transform)
                query.aoi = polygon_map
            except QgsCsException:
                pass

        self.browser.populate(query)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        self.browser.cancel_active_requests()

    def _on_listing_clicked(self, listing: Listing):
        """
        Triggered when a listing item is clicked
        """

        self.listing_details_pane = ListingDetailsWidget(listing)
        self.listing_details_pane.add_to_map.connect(self._add_listing_to_map)
        self.panel_stack.showPanel(self.listing_details_pane)

    def _add_listing_to_map(self, listing: Listing):
        """
        Called when a listing should be added to the map
        """
        if listing.listing_type != ListingType.TileLayer:
            # todo -- what to do with these?
            return

        if not listing.tile_url:
            # listing does not have tile url, so we need to request it now
            if self._current_listing_reply is not None and not sip.isdeleted(
                    self._current_listing_reply):
                self._current_listing_reply.abort()
                self._current_listing_reply = None

            request = API_CLIENT.request_listing(listing.id)
            self._current_listing_reply = QgsNetworkAccessManager.instance().get(request)
            self._current_listing_reply.finished.connect(
                partial(self._listing_reply_finished, self._current_listing_reply))
            return

        layer = listing.to_qgis_layer()
        if layer:
            QgsProject.instance().addMapLayer(layer)

    def _listing_reply_finished(self, reply: QNetworkReply):
        """
        Called on receiving a reply from the listing api
        """
        if sip.isdeleted(self):
            return

        if reply != self._current_listing_reply:
            # an old reply we don't care about anymore
            return

        self._current_listing_reply = None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return

        if reply.error() != QNetworkReply.NoError:
            print('error occurred :(')
            return

        listing = API_CLIENT.parse_listing_reply(reply)
        self._add_listing_to_map(listing)
