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
    def from_json(json: dict) -> 'Listing':
        """
        Creates a listing from JSON
        """
        return Listing()


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
        pass
