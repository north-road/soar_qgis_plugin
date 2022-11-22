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
    List
)

from qgis.PyQt.QtCore import (
    QDateTime
)
from qgis.core import QgsGeometry


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


class OrderBy(Enum):
    """
    Order by options
    """
    Views = 1
    Comments = 2
    Likes = 3
    Created = 4


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


class ApiClient:
    """
    API client for soar.earth API
    """

    URL = "https://api.soar-test.earth/v1"

    def __init__(self):
        pass

    def listings(self,
                 domain: str = 'soar.earth',
                 user_id: Optional[str] = None,
                 listing_type: Optional[ListingType] = None,
                 order_by: Optional[OrderBy] = None,
                 aoi: Optional[str] = None,  # todo -- rect/geom?
                 keywords: Optional[List[str]] = None,
                 category: Optional[str] = None,
                 featured: Optional[str] = None,
                 limit: int = 50,
                 offset: int = 0
                 ):
        """
        Retrieves listings for a set of parameters
        """
