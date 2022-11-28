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

import math
from functools import partial
from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QFontMetrics
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QSizePolicy
)
from qgis.core import QgsNetworkAccessManager
from qgis.gui import (
    QgsScrollArea,
    QgsPanelWidget
)


from .responsive_table_layout import ResponsiveTableWidget

from ..core.client import (
    ApiClient,
    Listing,
    ListingQuery
)

PAGE_SIZE = 20


class ListingsBrowserWidget(QgsPanelWidget):
    """
    A widget showing listings
    """

    total_count_changed = pyqtSignal(int)
    visible_count_changed = pyqtSignal(int)
    listing_clicked = pyqtSignal(Listing)

    def __init__(self):
        super().__init__()

        self.setPanelTitle(self.tr('Listings'))

        self.api_client = ApiClient()

        self.scroll_area = QgsScrollArea()
        self.scroll_area.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.table_widget = ResponsiveTableWidget()
        self.table_widget.listing_clicked.connect(self.listing_clicked)
        self.scroll_area.setWidget(self.table_widget)

        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        self.setObjectName('ListingsBrowserWidget')
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("#qt_scrollarea_viewport{ background: transparent; }")

        self._current_query: Optional[ListingQuery] = None
        self._current_reply: Optional[QNetworkReply] = None
        self._load_more_widget = None
        self._no_records_widget = None
        self._listings = []
        self.setMinimumWidth(370)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        if self._current_reply is not None and \
                not sip.isdeleted(self._current_reply):
            self._current_reply.abort()

        self._current_reply = None

    def _create_temporary_items_for_page(self):
        """
        Adds temporary items ready for the next page of results
        """
        for _ in range(PAGE_SIZE):
            self.table_widget.push_empty_widget()

    def populate(self, query: ListingQuery):
        """
        Populates the widget using a query
        """
        self.table_widget.setUpdatesEnabled(False)
        self.table_widget.clear()

        self._listings = []
        self._create_temporary_items_for_page()
        self.table_widget.setUpdatesEnabled(True)

        self._load_more_widget = None
        self._no_records_widget = None

        self.visible_count_changed.emit(-1)
        self._fetch_records(query)

    def _fetch_records(self,
                       query: Optional[ListingQuery] = None,
                       page: int = 1):
        """
        Fetches a page of records
        """
        if self._current_reply is not None and not sip.isdeleted(self._current_reply):
            self._current_reply.abort()
            self._current_reply = None

        if page == 1:
            # scroll to top on new search
            self.scroll_area.verticalScrollBar().setValue(0)

        if query is None:
            query = self._current_query

        query.limit = PAGE_SIZE
        query.offset = PAGE_SIZE * (page - 1)
        self._current_query = query

        request = self.api_client.request_listings(query)
        self._current_reply = QgsNetworkAccessManager.instance().get(request)
        self._current_reply.finished.connect(partial(self._reply_finished, self._current_reply))
        self.setCursor(Qt.WaitCursor)

    def _reply_finished(self, reply: QNetworkReply):
        """
        Called on receiving a reply from the listings api
        """
        if sip.isdeleted(self):
            return

        if reply != self._current_reply:
            # an old reply we don't care about anymore
            return

        self._current_reply = None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return

        if reply.error() != QNetworkReply.NoError:
            print('error occurred :(')
            return

        listings = self.api_client.parse_listings_reply(reply)

        self.table_widget.setUpdatesEnabled(False)

        for listing in listings:
            self.table_widget.push_listing(listing)

        self._listings.extend(listings)
        self.visible_count_changed.emit(len(self._listings))

        self.setCursor(Qt.ArrowCursor)
        self.table_widget.remove_empty_widgets()

        finished = len(listings) < PAGE_SIZE
        if not finished and not self._load_more_widget:
            self._load_more_widget = LoadMoreItemWidget()
            self._load_more_widget.load_more.connect(self.load_more)

            self.table_widget.push_widget(self._load_more_widget)

        elif finished and self._load_more_widget:
            self.table_widget.remove_widget(self._load_more_widget)
            self._load_more_widget = None

        if not self._listings and not self._no_records_widget:
            self._no_records_widget = NoRecordsItemWidget()
            self.table_widget.push_widget(self._no_records_widget)
        elif self._listings and self._no_records_widget:
            self.table_widget.remove_widget(self._no_records_widget)
            self._no_records_widget = None

        self.table_widget.setUpdatesEnabled(True)

    def load_more(self):
        """
        Loads the next page of results
        """
        next_page = math.ceil(len(self._listings) / PAGE_SIZE) + 1

        self.table_widget.remove_widget(self._load_more_widget)
        self._load_more_widget = None
        self._create_temporary_items_for_page()
        self._fetch_records(page=next_page)


class LoadMoreItemWidget(QFrame):
    """
    An item shown with a button for loading more results
    """
    load_more = pyqtSignal()

    def __init__(self):
        QFrame.__init__(self)
        self.load_more_button = QToolButton()
        self.load_more_button.setText(self.tr("Load more..."))
        self.load_more_button.clicked.connect(self.load_more)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.load_more_button)
        layout.addStretch()
        self.setLayout(layout)


class NoRecordsItemWidget(QFrame):
    """
    An item shown when no matching listings are available
    """

    def __init__(self):
        QFrame.__init__(self)
        self.no_data_frame = QLabel(self.tr("No data available"))

        self.no_data_frame.setStyleSheet(
            """
            QLabel {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 29px 23px 29px 23px;
                color: #a4a6a6;
                }
            """
        )

        top_padding = QFontMetrics(self.font()).height() * 3
        vl = QVBoxLayout()
        vl.addSpacing(top_padding)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.no_data_frame)
        layout.addStretch()
        vl.addLayout(layout)
        self.setLayout(vl)
