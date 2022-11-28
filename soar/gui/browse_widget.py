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
from functools import partial

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QTimer
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout
)
from qgis.PyQt.QtNetwork import QNetworkReply

from qgis.core import (
    QgsNetworkAccessManager
)

from qgis.gui import (
    QgsFilterLineEdit
)

from .listings_browser_widget import ListingsBrowserWidget
from ..core.client import (
    ApiClient,
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

        self.api_client = ApiClient()

        vl = QVBoxLayout()

        self.search_edit = QgsFilterLineEdit()
        self.search_edit.setShowSearchIcon(True)
        self.search_edit.setShowClearButton(True)
        self.search_edit.setPlaceholderText(self.tr('Search'))
        self.search_edit.textChanged.connect(self._filter_widget_changed)

        vl.addWidget(self.search_edit)

        self.browser = ListingsBrowserWidget()
        self.browser.listing_clicked.connect(self._on_listing_clicked)
        vl.addWidget(self.browser, 1)

        self.setLayout(vl)

        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout = QTimer(self)
        self._update_query_timeout.setSingleShot(True)
        self._update_query_timeout.timeout.connect(self._update_query)

        self._current_listing_reply: Optional[QNetworkReply] = None

    def _filter_widget_changed(self):
        """
        Triggered whenever any of the search filter widgets are changed
        """
        # changes to filter parameters are deferred to a small timeout, to avoid
        # starting lots of queries while a user is mid-operation (such as dragging a slider)
        self._update_query_timeout.start(500)

    def _update_query(self):
        """
        Updates the listings
        """
        query = ListingQuery(keywords=self.search_edit.text())
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
        if listing.listing_type != ListingType.TileLayer:
            # todo -- what to do with these?
            return

        if not listing.tile_url:
            # listing does not have tile url, so we need to request it now
            if self._current_listing_reply is not None and not sip.isdeleted(self._current_listing_reply):
                self._current_listing_reply.abort()
                self._current_listing_reply = None

            request = self.api_client.request_listing(listing.id)
            self._current_listing_reply = QgsNetworkAccessManager.instance().get(request)
            self._current_listing_reply.finished.connect(
                partial(self._listing_reply_finished, self._current_listing_reply))
            return

        layer = listing.to_qgis_layer()
        if layer:
            from qgis.core import QgsProject
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

        listing = self.api_client.parse_listing_reply(reply)
        self._on_listing_clicked(listing)
