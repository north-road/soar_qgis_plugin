# coding=utf-8
"""soar.earth API client Test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = '(C) 2022 by Nyall Dawson'
__date__ = '23/11/2022'
__copyright__ = 'Copyright 2022, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import unittest

from .utilities import get_qgis_app
from ..core.client import (
    Listing,
    ListingType
)

QGIS_APP = get_qgis_app()


class ApiClientTest(unittest.TestCase):
    """Test API client work."""

    def test_listing_from_json(self):
        json = {
            "owner": "4515f58126704ae4831ffa9d66c395d7",
            "metadata": "{\"description\":\"Creative application of Sentinel 2 water quality script and b/w Google satellite imagery\",\"category\":\"satellite\",\"title\":\"Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019\",\"tc\":true,\"tags\":[]}",
            "previewUrl": "https://short-preview.soar.earth/preview%2Fbrowser%2Fprod%2F4515f58126704ae4831ffa9d66c395d7%40soar%2Fyamchi+dam_8ab6c81cd0d07457796a87da86a7ae38.tiff.png",
            "avatarUrl": "https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview",
            "description": "Creative application of Sentinel 2 water quality script and b/w Google satellite imagery",
            "minZoom": 12,
            "listingType": "TILE_LAYER",
            "title": "Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019",
            "userName": "TheRealDazzler",
            "userId": "4515f58126704ae4831ffa9d66c395d7",
            "tags": ['flood', 'emergency'],
            "createdAt": 1630467771,
            "totalComments": 1,
            "filename": "browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi dam_8ab6c81cd0d07457796a87da86a7ae38.tiff",
            "totalViews": 13,
            "id": 10465,
            "filehash": "8ab6c81cd0d07457796a87da86a7ae38",
            "totalLikes": 33,
            "categories": [
                "marine",
                "environment"
            ],
            "geometryWKT": "POLYGON((48.10236963 38.07218305,48.03699668 38.07218305,48.03699668 38.03425478,48.10236963 38.03425478,48.10236963 38.07218305))",
            "updatedAt": 1666322734
        }

        listing = Listing.from_json(json)
        self.assertEqual(listing.owner, '4515f58126704ae4831ffa9d66c395d7')
        self.assertEqual(listing.metadata, {
            "description": "Creative application of Sentinel 2 water quality script and b/w Google satellite imagery",
            "category": "satellite",
            "title": "Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019",
            "tc": True,
            "tags": []})
        self.assertEqual(listing.preview_url,
                         'https://short-preview.soar.earth/preview%2Fbrowser%2Fprod%2F4515f58126704ae4831ffa9d66c395d7%40soar%2Fyamchi+dam_8ab6c81cd0d07457796a87da86a7ae38.tiff.png')
        self.assertEqual(listing.avatar_url,
                         'https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview')
        self.assertEqual(listing.description,
                         'Creative application of Sentinel 2 water quality script and b/w Google satellite imagery')
        self.assertEqual(listing.min_zoom, 12)
        self.assertEqual(listing.listing_type, ListingType.TileLayer)
        self.assertEqual(listing.title,
                         'Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019')
        self.assertEqual(listing.user_name, 'TheRealDazzler')
        self.assertEqual(listing.user_id, '4515f58126704ae4831ffa9d66c395d7')
        self.assertEqual(listing.tags, ['flood', 'emergency'])
        # self.assertEqual(listing.created_at, '')
        self.assertEqual(listing.total_comments, 1)
        self.assertEqual(listing.filename,
                         "browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi dam_8ab6c81cd0d07457796a87da86a7ae38.tiff")
        self.assertEqual(listing.total_views, 13)
        self.assertEqual(listing.id, 10465)
        self.assertEqual(listing.filehash, '8ab6c81cd0d07457796a87da86a7ae38')
        self.assertEqual(listing.total_likes, 33)
        self.assertEqual(listing.categories, ['marine', 'environment'])
        # self.assertEqual(listing.geometry, '')
        # self.assertEqual(listing.updated_at, '')


if __name__ == "__main__":
    suite = unittest.makeSuite(ApiClientTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
