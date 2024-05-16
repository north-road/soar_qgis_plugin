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
from functools import partial

from qgis.PyQt.QtCore import (
    Qt,
    QDateTime, QDate, QTime)
from qgis.PyQt.QtTest import QSignalSpy
from qgis.core import (
    QgsGeometry,
    QgsNetworkAccessManager
)

from .utilities import get_qgis_app
from ..core.client import (
    Listing,
    User,
    ListingType,
    ApiClient,
    OrderBy,
    ListingQuery
)

QGIS_APP = get_qgis_app()


class ApiClientTest(unittest.TestCase):
    """Test API client work."""

    def test_user_from_json(self):
        """
        Test creating User from JSON
        """
        json = {
            "createdAt": 1571710337,
            "avatarUrl": "https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview",
            "name": "TheRealDazzler",
            "userId": "4515f58126704ae4831ffa9d66c395d7",
            "ethAddress": "1234"
        }

        user = User.from_json(json)
        self.assertEqual(user.created_at.toUTC(),
                         QDateTime(QDate(2019, 10, 22), QTime(2, 12, 17, 0), Qt.TimeSpec(1)))
        self.assertEqual(user.avatar_url,
                         'https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview')
        self.assertEqual(user.name, 'TheRealDazzler')
        self.assertEqual(user.user_id, '4515f58126704ae4831ffa9d66c395d7')
        self.assertEqual(user.eth_address, '1234')

    def test_listing_from_json(self):
        """
        Test creating Listing from JSON, using the form returned by the Listings api
        """
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
            "updatedAt": 1669153356
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
        self.assertEqual(listing.user.avatar_url,
                         'https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview')
        self.assertEqual(listing.user.name, 'TheRealDazzler')
        self.assertEqual(listing.user.user_id, '4515f58126704ae4831ffa9d66c395d7')
        self.assertEqual(listing.description,
                         'Creative application of Sentinel 2 water quality script and b/w Google satellite imagery')
        self.assertEqual(listing.min_zoom, 12)
        self.assertEqual(listing.listing_type, ListingType.TileLayer)
        self.assertEqual(listing.title,
                         'Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019')
        self.assertEqual(listing.tags, ['flood', 'emergency'])
        self.assertEqual(listing.created_at.toUTC(),
                         QDateTime(QDate(2021, 9, 1), QTime(3, 42, 51, 0), Qt.TimeSpec(1)))
        self.assertEqual(listing.total_comments, 1)
        self.assertEqual(listing.filename,
                         "browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi dam_8ab6c81cd0d07457796a87da86a7ae38.tiff")
        self.assertEqual(listing.total_views, 13)
        self.assertEqual(listing.id, 10465)
        self.assertEqual(listing.filehash, '8ab6c81cd0d07457796a87da86a7ae38')
        self.assertEqual(listing.total_likes, 33)
        self.assertEqual(listing.categories, ['marine', 'environment'])
        self.assertEqual(listing.geometry.asWkt(1),
                         'Polygon ((48.1 38.1, 48 38.1, 48 38, 48.1 38, 48.1 38.1))')
        self.assertEqual(listing.updated_at.toUTC(),
                         QDateTime(QDate(2022, 11, 22), QTime(21, 42, 36, 0), Qt.TimeSpec(1)))

    def test_listing_from_json_singular(self):
        """
        Test creating Listing from JSON, using the form returned by the Listing api
        """
        json = {
            "tileUrl": "https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z={z}&x={x}&y={y}&access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw&dom=1",
            "metadata": "{\"description\":\"Creative application of Sentinel 2 water quality script and b/w Google satellite imagery\",\"category\":\"satellite\",\"title\":\"Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019\",\"tc\":true,\"tags\":[]}",
            "previewUrl": "https://short-preview.soar.earth/preview%2Fbrowser%2Fprod%2F4515f58126704ae4831ffa9d66c395d7%40soar%2Fyamchi__8ab6c81cd0d07457796a87da86a7ae38.tif.png",
            "description": "Creative application of Sentinel 2 water quality script and b/w Google satellite imagery",
            "listingType": "TILE_LAYER",
            "filesize": 3894594,
            "title": "Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019",
            "createdAt": 1630467763,
            "price": {
                "priceUsd": 0,
                "feeUsd": 0.3,
                "priceSkym": 0
            },
            "id": 10464,
            "categories": [
                "environment",
                "marine"
            ],
            "listing": {
                "owner": "4515f58126704ae4831ffa9d66c395d7",
                "tileUrl": "https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z={z}&x={x}&y={y}&access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw&dom=1",
                "metadata": "{\"description\":\"Creative application of Sentinel 2 water quality script and b/w Google satellite imagery\",\"category\":\"satellite\",\"title\":\"Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019\",\"tc\":true,\"tags\":[]}",
                "previewUrl": "https://short-preview.soar.earth/preview%2Fbrowser%2Fprod%2F4515f58126704ae4831ffa9d66c395d7%40soar%2Fyamchi__8ab6c81cd0d07457796a87da86a7ae38.tif.png",
                "listingType": "TILE_LAYER",
                "filesize": 3894594,
                "url": "https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z={z}&x={x}&y={y}&access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw&dom=1",
                "createdAt": 1630467763,
                "filename": "browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif",
                "price": {
                    "priceUsd": 0,
                    "feeUsd": 0.3,
                    "priceSkym": 0
                },
                "pointWKT": "POLYGON((48.10236963 38.07218305,48.03699668 38.07218305,48.03699668 38.03425478,48.10236963 38.03425478,48.10236963 38.07218305))",
                "uploadedAt": 1630467763,
                "id": 10464,
                "filehash": "8ab6c81cd0d07457796a87da86a7ae38",
                "totalLikes": 9,
                "geometryWKT": "POLYGON((48.10236963 38.07218305,48.03699668 38.07218305,48.03699668 38.03425478,48.10236963 38.03425478,48.10236963 38.07218305))",
                "updatedAt": 1666322742
            },
            "geometryWKT": "POLYGON((48.10236963 38.07218305,48.03699668 38.07218305,48.03699668 38.03425478,48.10236963 38.03425478,48.10236963 38.07218305))",
            "updatedAt": 1666322742,
            "owner": "4515f58126704ae4831ffa9d66c395d7",
            "avatarUrl": "https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview",
            "minZoom": 12,
            "userName": "TheRealDazzler",
            "userId": "4515f58126704ae4831ffa9d66c395d7",
            "tags": ['flood', 'emergency'],
            "filename": "browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif",
            "totalComments": 1,
            "domainName": "soar.earth",
            "files": [],
            "totalViews": 9,
            "filehash": "8ab6c81cd0d07457796a87da86a7ae38",
            "totalLikes": 33,
            "tileUrlExpiryAt": 1669996817,
            "user": {
                "createdAt": 1571710337,
                "avatarUrl": "https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview",
                "name": "TheRealDazzler",
                "userId": "4515f58126704ae4831ffa9d66c395d7",
                "ethAddress": "4515f58126704ae4831ffa9d66c395d7"
            },
            "reviewSoar": "APPROVED"
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
                         'https://short-preview.soar.earth/preview%2Fbrowser%2Fprod%2F4515f58126704ae4831ffa9d66c395d7%40soar%2Fyamchi__8ab6c81cd0d07457796a87da86a7ae38.tif.png')
        self.assertEqual(listing.user.avatar_url,
                         'https://avatar.soar.earth/4515f58126704ae4831ffa9d66c395d7wtm.png/preview')
        self.assertEqual(listing.user.name, 'TheRealDazzler')
        self.assertEqual(listing.user.user_id, '4515f58126704ae4831ffa9d66c395d7')
        self.assertEqual(listing.description,
                         'Creative application of Sentinel 2 water quality script and b/w Google satellite imagery')
        self.assertEqual(listing.min_zoom, 12)
        self.assertEqual(listing.listing_type, ListingType.TileLayer)
        self.assertEqual(listing.title,
                         'Cyanobacteria Levels, Near flood-stage Yamchi Dam, Iran June 10, 2019')
        self.assertEqual(listing.tags, ['flood', 'emergency'])
        self.assertEqual(listing.created_at.toUTC(),
                         QDateTime(QDate(2021, 9, 1), QTime(3, 42, 43, 0), Qt.TimeSpec(1)))
        self.assertEqual(listing.total_comments, 1)
        self.assertEqual(listing.filename,
                         "browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif")
        self.assertEqual(listing.total_views, 9)
        self.assertEqual(listing.id, 10464)
        self.assertEqual(listing.filehash, '8ab6c81cd0d07457796a87da86a7ae38')
        self.assertEqual(listing.total_likes, 33)
        self.assertEqual(listing.categories, ['environment', 'marine'])
        self.assertEqual(listing.geometry.asWkt(1),
                         'Polygon ((48.1 38.1, 48 38.1, 48 38, 48.1 38, 48.1 38.1))')
        self.assertEqual(listing.updated_at.toUTC(),
                         QDateTime(QDate(2022, 10, 21), QTime(3, 25, 42, 0), Qt.TimeSpec(1)))

        self.assertEqual(listing.tile_url,
                         'https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z={z}&x={x}&y={y}&access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw&dom=1')
        self.assertEqual(listing.file_size, 3894594)
        self.assertEqual(listing.domain_name, 'soar.earth')
        self.assertEqual(listing.tile_url_expiry_at.toUTC(),
                         QDateTime(QDate(2022, 12, 2), QTime(16, 0, 17, 0), Qt.TimeSpec(1)))

    def test_listing_to_layer(self):
        """
        Test converting a listing to a QGIS layer
        """
        listing = Listing()
        listing.min_zoom = 15
        listing.geometry = QgsGeometry.fromWkt(
            'Polygon ((48.1 38.1, 48 38.1, 48 38, 48.1 38, 48.1 38.1))')
        listing.tile_url = 'https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z={z}&x={x}&y={y}&access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw&dom=1'

        # we have to ignore min zoom for values >= 18, as this will cause QGIS
        # to render nothing for the layer
        listing.min_zoom = 18
        self.assertEqual(listing.to_qgis_layer_source_string(),
                         'type=xyz&url=https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z%3D%7Bz%7D%26x%3D%7Bx%7D%26y%3D%7B-y%7D%26access_token%3DeyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw%26dom%3D1')

        listing.min_zoom = 15
        self.assertEqual(listing.to_qgis_layer_source_string(),
                         'type=xyz&url=https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z%3D%7Bz%7D%26x%3D%7Bx%7D%26y%3D%7B-y%7D%26access_token%3DeyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw%26dom%3D1&zmin=15')

        layer = listing.to_qgis_layer()
        self.assertEqual(layer.providerType(), 'wms')
        self.assertEqual(layer.source(),
                         'type=xyz&url=https://shared-tile.soar.earth/images/browser/prod/4515f58126704ae4831ffa9d66c395d7@soar/yamchi__8ab6c81cd0d07457796a87da86a7ae38.tif/tile?z%3D%7Bz%7D%26x%3D%7Bx%7D%26y%3D%7B-y%7D%26access_token%3DeyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJ3a3QiOiJQT0xZR09OKCg0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wNzIxODMwNSw0OC4wMzY5OTY2OCAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wMzQyNTQ3OCw0OC4xMDIzNjk2MyAzOC4wNzIxODMwNSkpIiwiaXNzIjoiYXBpLnNvYXIuZWFydGgiLCJtaW5ab29tIjoxMCwiZXhwIjoxNjY5OTk2ODE3LCJpYXQiOjE2NjkyMTkyMTcsInVzZXJJZCI6InN5c3RlbSIsImp0aSI6IjIxOTY2OWQwNDYyZTQ0ZmQ5NzU3MDQ5YzVlM2I5MDEyIiwia2V5IjoiYnJvd3Nlci9wcm9kLzQ1MTVmNTgxMjY3MDRhZTQ4MzFmZmE5ZDY2YzM5NWQ3QHNvYXIveWFtY2hpX184YWI2YzgxY2QwZDA3NDU3Nzk2YTg3ZGE4NmE3YWUzOC50aWYiLCJzdGF0dXMiOiJPSyJ9.TxZ9Q6pxLCxufAWlmoTOFaMsLv3QepIDTbz3otA7SHq2hfjn4JKSBKRq1736RQoLMHXoGuRPV289AEpHRbbb9CGj77oUpFralbQckvBKzcsxqTfrT3oGv8Dl-U5zWIQ2iy6BNKE1zuFcX2imQAq-wco6dUHkr1HjpqOR1XCwLM0B9Pt90Sm2Mb7CL7jICLhOs1aSLwSn473_pfobWyd8PCZQr_1I4lSSuRGNb2KbZ67LeAbCYX2lpLuSUbIv4lqHwPipX75w4SAxtgSxjctEptrKsefMJpHpdd-zIeUyn3Hf0VHzOwjmIhQoNdo-16VTn2i6wDc2J9XZl0s3Glsyzw%26dom%3D1&zmin=15')
        self.assertAlmostEqual(layer.extent().xMinimum(), 5343335, -3)
        self.assertAlmostEqual(layer.extent().xMaximum(), 5354467, -3)
        self.assertAlmostEqual(layer.extent().yMinimum(), 4579425, -3)
        self.assertAlmostEqual(layer.extent().yMaximum(), 4593562, -3)

    def test_listings_request(self):
        """
        Test building listings requests
        """
        client = ApiClient()

        query = ListingQuery(limit=2, keywords='flood',
                             user_id='4515f58126704ae4831ffa9d66c395d7')
        query.listing_types = None
        request = client.request_listings(query)
        self.assertEqual(request.url().toString(),
                         'https://api.soar.earth/v1/listings?keywords=flood&userId=4515f58126704ae4831ffa9d66c395d7&limit=2')
        self.assertEqual(request.rawHeader(b'Subdomain'), b'soar.earth')

        query = ListingQuery(
            listing_types=[ListingType.Wms],
            order_by=OrderBy.Comments,
            keywords='flood',
            category='categ',
            featured='feat',
            offset=5)
        request = client.request_listings(query, domain='test.earth')
        self.assertEqual(request.rawHeader(b'Subdomain'), b'test.earth')
        self.assertEqual(request.url().toString(),
                         'https://api.soar.earth/v1/listings?keywords=flood&limit=50&offset=5&listingType=WMS&orderBy=COMMENTS&category=categ&featured=feat')

        query = ListingQuery(
            listing_types=[ListingType.Wms, ListingType.TileLayer],
            order_by=OrderBy.Comments,
            keywords='flood',
            category='categ',
            featured='feat',
            offset=5)
        request = client.request_listings(query, domain='test.earth')
        self.assertEqual(request.rawHeader(b'Subdomain'), b'test.earth')
        self.assertEqual(request.url().toString(),
                         'https://api.soar.earth/v1/listings?keywords=flood&limit=50&offset=5&listingType=WMS,TILE_LAYER&orderBy=COMMENTS&category=categ&featured=feat')

        query = ListingQuery(aoi=QgsGeometry.fromWkt(
            'POLYGON ((15.813616 49.501767, 15.670471 49.501767, 15.670471 49.397561, 15.813616 49.397561, 15.813616 49.501767))]'))
        request = client.request_listings(query)
        self.assertEqual(request.url().toString(),
                         'https://api.soar.earth/v1/listings?limit=50&listingType=TILE_LAYER&aoi=POLYGON '
                         '((15.8136 49.5018, 15.6705 49.5018, 15.6705 49.3976, 15.8136 49.3976, 15.8136 49.5018))')

    # pylint: disable=attribute-defined-outside-init

    def test_listings_reply(self):
        """
        Test handling listings replies
        """
        client = ApiClient()
        query = ListingQuery(limit=2, keywords='flood',
                             user_id='4515f58126704ae4831ffa9d66c395d7')
        request = client.request_listings(query)
        reply = QgsNetworkAccessManager.instance().get(request)
        self._result = None

        def finished(_reply):
            self._result = client.parse_listings_reply(_reply)

        reply.finished.connect(partial(finished, reply))
        spy = QSignalSpy(reply.finished)
        spy.wait()

        self.assertEqual(len(self._result), 2)
        self.assertEqual(self._result[0].id, 10464)
        self.assertEqual(self._result[1].id, 9966)

    def test_aoi(self):
        """
        Test aoi WKT generation
        """
        query = ListingQuery()
        query.aoi = QgsGeometry.fromWkt(
            'Polygon ((17820279 -4473060, 17066712 -4972615, 17401161 -5400201, 18463774 -5281662, 17820279 -4473060))')
        params = query.to_query_parameters()
        self.assertEqual(params, {
            'aoi': 'POLYGON ((17820279 -4473060, 17066712 -4972615, 17401161 -5400201, '
                   '18463774 -5281662, 17820279 -4473060))',
            'limit': 50,
            'listingType': 'TILE_LAYER'})

    def test_listing_request(self):
        """
        Test building listing requests
        """
        client = ApiClient()

        request = client.request_listing(10464)
        self.assertEqual(request.url().toString(),
                         'https://api.soar.earth/v1/listings/10464')
        self.assertEqual(request.rawHeader(b'Subdomain'), b'soar.earth')

        request = client.request_listing(10464, domain='test.earth')
        self.assertEqual(request.rawHeader(b'Subdomain'), b'test.earth')
        self.assertEqual(request.url().toString(),
                         'https://api.soar.earth/v1/listings/10464')

    def test_listing_reply(self):
        """
        Test handling listing replies
        """
        client = ApiClient()
        request = client.request_listing(10464)
        reply = QgsNetworkAccessManager.instance().get(request)
        self._result = None

        def finished(_reply):
            self._result = client.parse_listing_reply(_reply)

        reply.finished.connect(partial(finished, reply))
        spy = QSignalSpy(reply.finished)
        spy.wait()

        self.assertIsInstance(self._result, Listing)
        self.assertEqual(self._result.id, 10464)
        self.assertEqual(self._result.file_size, 3894594)


if __name__ == "__main__":
    suite = unittest.makeSuite(ApiClientTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
