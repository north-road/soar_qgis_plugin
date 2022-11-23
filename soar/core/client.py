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

import json
from enum import Enum
from typing import (
    Optional,
    List,
    Dict
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    pyqtSignal,
    QObject,
    QDateTime,
    QUrl,
    QUrlQuery
)
from qgis.PyQt.QtNetwork import (
    QNetworkRequest,
    QNetworkReply
)
from qgis.core import (
    QgsGeometry
)


class ListingType(Enum):
    """
    Listing types
    """
    TileLayer = 1
    Image = 2
    Wms = 3
    Order = 4

    @staticmethod
    def from_string(string: Optional[str]) -> Optional['ListingType']:
        """
        Converts a string to a ListingType
        """
        if not string:
            return None
        return {'TILE_LAYER': ListingType.TileLayer,
                'IMAGE': ListingType.Image,
                'WMS': ListingType.Wms,
                'ORDER': ListingType.Order
                }[string]

    @staticmethod
    def to_string(listing: 'Listing') -> str:
        """
        Converts a listing value to string
        """
        return {ListingType.TileLayer: 'TILE_LAYER',
                ListingType.Image: 'IMAGE',
                ListingType.Wms: 'WMS',
                ListingType.Order: 'ORDER'
                }[listing]


class OrderBy(Enum):
    """
    Order by options
    """
    Views = 1
    Comments = 2
    Likes = 3
    Created = 4

    @staticmethod
    def to_string(order_by: 'OrderBy') -> str:
        """
        Converts a order by value to string
        """
        return {OrderBy.Views: 'VIEWS',
                OrderBy.Comments: 'COMMENTS',
                OrderBy.Likes: 'LIKES',
                OrderBy.Created: 'CREATED'
                }[order_by]


class Listing:
    """
    Encapsulates a soar.earth dataset listing
    """

    def __init__(self):
        self.owner: Optional[str] = None
        self.metadata = {}
        self.preview_url: Optional[str] = None
        self.avatar_url: Optional[str] = None
        self.description: Optional[str] = None
        self.min_zoom: Optional[int] = None
        self.listing_type: ListingType = ListingType.TileLayer
        self.title: Optional[str] = None
        self.user_name: Optional[str] = None
        self.user_id: Optional[str] = None
        self.tags: List[str] = []
        self.created_at: QDateTime = QDateTime()
        self.total_comments: int = 0
        self.filename: Optional[str] = None
        self.total_views: int = 0
        self.id: int = 0
        self.filehash: Optional[str] = None
        self.total_likes: int = 0
        self.categories: List[str] = []
        self.geometry: Optional[QgsGeometry] = None
        self.updated_at: QDateTime = QDateTime()

    def __repr__(self):
        return f'<Listing: "{self.title}">'

    @staticmethod
    def from_json(input_json: dict) -> 'Listing':
        """
        Creates a listing from JSON
        """
        res = Listing()
        res.owner = input_json.get('owner')
        metadata_json = input_json.get('metadata')
        if metadata_json:
            res.metadata = json.loads(metadata_json)
        res.preview_url = input_json.get('previewUrl')
        res.avatar_url = input_json.get('avatarUrl')
        res.description = input_json.get('description')
        min_zoom = input_json.get('minZoom')
        if min_zoom:
            res.min_zoom = int(min_zoom)
        res.listing_type = ListingType.from_string(input_json.get('listingType'))
        res.title = input_json.get('title')
        res.user_name = input_json.get('userName')
        res.user_id = input_json.get('userId')
        res.tags = input_json.get('tags', [])
        created_at_seconds = input_json.get('createdAt')
        if created_at_seconds is not None:
            res.created_at = QDateTime.fromSecsSinceEpoch(int(created_at_seconds))
        total_comments = input_json.get('totalComments')
        if total_comments is not None:
            res.total_comments = int(total_comments)
        res.filename = input_json.get('filename')
        total_views = input_json.get('totalViews')
        if total_views is not None:
            res.total_views = int(total_views)
        _id = input_json.get('id')
        if _id is not None:
            res.id = int(_id)
        res.filehash = input_json.get('filehash')
        total_likes = input_json.get('totalLikes')
        if total_likes is not None:
            res.total_likes = int(total_likes)
        res.categories = input_json.get('categories', [])
        wkt = input_json.get('geometryWKT')
        if wkt:
            res.geometry = QgsGeometry.fromWkt(wkt)

        updated_at_seconds = input_json.get('updatedAt')
        if updated_at_seconds is not None:
            res.updated_at = QDateTime.fromSecsSinceEpoch(int(updated_at_seconds))
        return res


class ListingQuery:
    """
    Represents a listing query
    """

    def __init__(self,
                 user_id: Optional[str] = None,
                 listing_type: Optional[ListingType] = None,
                 order_by: Optional[OrderBy] = None,
                 aoi: Optional[QgsGeometry] = None,
                 keywords: Optional[str] = None,
                 category: Optional[str] = None,
                 featured: Optional[str] = None,
                 limit: int = 50,
                 offset: int = 0):
        self.user_id: Optional[str] = user_id
        self.listing_type: Optional[ListingType] = listing_type
        self.order_by: Optional[OrderBy] = order_by
        self.aoi: Optional[QgsGeometry] = aoi
        self.keywords: Optional[str] = keywords
        self.category: Optional[str] = category
        self.featured: Optional[str] = featured
        self.limit: int = limit
        self.offset: int = offset

    def to_query_parameters(self) -> dict:
        """
        Converts the query to a dictionary of query parameters
        """
        params = {}
        if self.keywords:
            params['keywords'] = self.keywords
        if self.user_id:
            params['userId'] = self.user_id
        if self.limit:
            params['limit'] = self.limit
        if self.offset:
            params['offset'] = self.offset
        if self.listing_type:
            params['listingType'] = ListingType.to_string(self.listing_type)
        if self.order_by:
            params['orderBy'] = OrderBy.to_string(self.order_by)
        if self.category:
            params['category'] = self.category
        if self.featured:
            params['featured'] = self.featured
        if self.aoi and not self.aoi.isEmpty():
            params['aoi'] = self.aoi.asWkt()
        return params


class ApiClient(QObject):
    """
    API client for soar.earth API
    """

    URL = "https://api.soar.earth/v1"
    LISTINGS_ENDPOINT = 'listings'

    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # standard headers to add to all requests
        self.headers = {
            'Subdomain': 'soar.earth',
            'accept': 'application/json'
        }

    def request_listings(self,
                         query: ListingQuery,
                         domain: str = 'soar.earth',
                         ) -> QNetworkRequest:
        """
        Retrieves listings for a set of parameters (async)

        The returned network request must be retrieved via QgsNetworkAccessManager,
        and the reply parsed by parse_listings_reply
        """
        params = query.to_query_parameters()

        headers = {}
        if domain:
            headers = {
                'Subdomain': domain
            }
        network_request = self._build_request(self.LISTINGS_ENDPOINT, headers, params)

        return network_request

    def parse_listings_reply(self, reply: QNetworkReply) -> List[Listing]:
        """
        Parse a listings reply and return as a list of Listings objects
        """
        if sip.isdeleted(self):
            print('deleted')
            return []

        if reply.error() == QNetworkReply.OperationCanceledError:
            print('canceled')
            return []

        if reply.error() != QNetworkReply.NoError:
            self.error_occurred.emit(reply.errorString())
            return []

        listings_json = json.loads(reply.readAll().data().decode())['listings']
        return [Listing.from_json(listing) for listing in listings_json]

    @staticmethod
    def _to_url_query(parameters: Dict[str, object]) -> QUrlQuery:
        """
        Converts query parameters as a dictionary to a URL query
        """
        query = QUrlQuery()
        for name, value in parameters.items():
            if isinstance(value, (list, tuple)):
                for v in value:
                    query.addQueryItem(name, str(v))
            else:
                query.addQueryItem(name, str(value))
        return query

    def _build_request(self, endpoint: str, headers=None, params=None) -> QNetworkRequest:
        """
        Builds a network request
        """
        url = QUrl(f"{self.URL}/{endpoint}")

        if params:
            url.setQuery(ApiClient._to_url_query(params))

        network_request = QNetworkRequest(url)

        combined_headers = self.headers
        if headers:
            combined_headers.update(headers)

        for header, value in combined_headers.items():
            network_request.setRawHeader(header.encode(), value.encode())

        return network_request
