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
from pathlib import Path
from typing import (
    Optional,
    List,
    Dict,
    Tuple
)

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    pyqtSignal,
    Qt,
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
    Qgis,
    QgsBox3d,
    QgsGeometry,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsLayerMetadata,
    QgsAbstractMetadataBase,
    QgsNetworkAccessManager
)

from .map_exporter import MapExportSettings


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


class User:
    """
    Encapsulates a soar.earth user
    """

    def __init__(self):
        self.created_at: QDateTime = QDateTime()
        self.avatar_url: Optional[str] = None
        self.name: Optional[str] = None
        self.user_id: Optional[str] = None
        self.eth_address: Optional[str] = None

    def __repr__(self):
        return f'<User: "{self.name}">'

    def permalink(self) -> str:
        """
        Returns a permalink for the user
        """
        return f'https://soar.earth/profile/{self.user_id}'

    @staticmethod
    def from_json(input_json: dict) -> 'User':
        """
        Creates a user from JSON
        """
        res = User()

        created_at_seconds = input_json.get('createdAt')
        if created_at_seconds is not None:
            res.created_at = QDateTime.fromSecsSinceEpoch(int(created_at_seconds))

        res.avatar_url = input_json.get('avatarUrl')
        res.name = input_json.get('name')
        res.user_id = input_json.get('userId')
        res.eth_address = input_json.get('ethAddress')

        return res


class Listing:
    """
    Encapsulates a soar.earth dataset listing
    """

    def __init__(self):
        self.owner: Optional[str] = None
        self.metadata = {}
        self.preview_url: Optional[str] = None
        self.user: Optional[User] = None
        self.description: Optional[str] = None
        self.min_zoom: Optional[int] = None
        self.listing_type: ListingType = ListingType.TileLayer
        self.title: Optional[str] = None
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
        self.tile_url: Optional[str] = None
        self.file_size: Optional[int] = None
        self.domain_name: Optional[str] = None
        self.files: List[str] = []
        self.tile_url_expiry_at: QDateTime = QDateTime()

    def __repr__(self):
        return f'<Listing: "{self.title}">'

    def permalink(self) -> str:
        """
        Returns a permalink for the listing
        """
        return f'https://soar.earth/maps/{self.id}'

    def to_qgis_layer_source_string(self) -> Optional[str]:
        """
        Returns a qgis layer source string file the listing
        """
        source_uri = self.tile_url
        if not source_uri:
            return None

        source_uri = source_uri.replace('{y}', '{-y}')
        source_uri = source_uri.replace('&', '%26')
        source_uri = source_uri.replace('=', '%3D')
        source_uri = source_uri.replace('{', '%7B')
        source_uri = source_uri.replace('}', '%7D')

        layer_uri = f"type=xyz&url={source_uri}"
        if self.min_zoom is not None:
            layer_uri += f'&zmin={self.min_zoom}'

        return layer_uri

    def to_layer_metadata(self) -> Optional[QgsLayerMetadata]:
        """
        Converts the listing to QGIS layer metadata
        """
        res = QgsLayerMetadata()
        if self.id:
            res.setIdentifier(str(self.id))
        res.setType('dataset')
        res.setTitle(self.title)
        res.setAbstract(self.description)
        res.setLanguage('en')
        if self.tags:
            res.addKeywords('tags', self.tags)
        res.setCategories(self.categories)

        link = QgsAbstractMetadataBase.Link()
        link.name = 'Dataset'
        link.type = 'WWW:LINK'
        link.description = self.title
        link.url = self.permalink()
        res.addLink(link)

        if self.user:
            link = QgsAbstractMetadataBase.Link()
            link.name = 'Author'
            link.type = 'WWW:LINK'
            link.description = self.user.name
            link.url = self.user.permalink()
            res.addLink(link)

        if self.created_at and self.created_at.isValid():
            try:
                res.setDateTime(Qgis.MetadataDateType.Created, self.created_at)
                res.setDateTime(Qgis.MetadataDateType.Published, self.created_at)
            except AttributeError:
                # requires QGIS 3.30+
                pass
        if self.updated_at and self.updated_at.isValid():
            try:
                res.setDateTime(Qgis.MetadataDateType.Revised, self.updated_at)
            except AttributeError:
                # requires QGIS 3.30+
                pass

        if self.user:
            author = QgsAbstractMetadataBase.Contact()
            author.name = self.user.name
            author.role = 'author'
            res.addContact(author)

        if self.geometry and not self.geometry.isEmpty():
            extent = QgsLayerMetadata.Extent()
            spatial_extent = QgsLayerMetadata.SpatialExtent()
            spatial_extent.extentCrs = QgsCoordinateReferenceSystem('EPSG:4326')
            spatial_extent.bounds = QgsBox3d(self.geometry.boundingBox())
            extent.setSpatialExtents([spatial_extent])
            res.setExtent(extent)

        res.setCrs(QgsCoordinateReferenceSystem('EPSG:3857'))

        # todo license? use constraints? link?
        return res

    def to_qgis_layer(self) -> Optional[QgsRasterLayer]:
        """
        Returns a QgsRasterLayer for the listing
        """
        layer_uri = self.to_qgis_layer_source_string()
        if not layer_uri:
            return None

        layer = QgsRasterLayer(layer_uri, self.title, 'wms')

        # avoid server load by disabling prefetch preview jobs
        layer.setCustomProperty('rendering/noPreviewJobs', True)

        # force set the layer's extent to what we know the extent will be, because otherwise QGIS
        # will assume it is global
        if self.geometry and not self.geometry.isEmpty():
            transform = QgsCoordinateTransform(
                QgsCoordinateReferenceSystem('EPSG:4326'),
                QgsCoordinateReferenceSystem('EPSG:3857'),
                QgsProject.instance())
            extent_3857 = transform.transformBoundingBox(self.geometry.boundingBox())
            layer.setExtent(extent_3857)

        layer.setMetadata(self.to_layer_metadata())

        layer.setCustomProperty('_soar_layer_id', self.id)
        if self.tile_url_expiry_at:
            layer.setCustomProperty('_soar_layer_expiry',
                                    self.tile_url_expiry_at.toString(Qt.ISODate))

        return layer

    @staticmethod
    def from_json(input_json: dict) -> 'Listing':  # pylint:disable=too-many-statements
        """
        Creates a listing from JSON
        """
        res = Listing()
        res.owner = input_json.get('owner')
        metadata_json = input_json.get('metadata')
        if metadata_json:
            res.metadata = json.loads(metadata_json)
        res.preview_url = input_json.get('previewUrl')
        res.description = input_json.get('description')
        min_zoom = input_json.get('minZoom')
        if min_zoom:
            res.min_zoom = int(min_zoom)
        res.listing_type = ListingType.from_string(input_json.get('listingType'))
        res.title = input_json.get('title')

        if 'userId' in input_json:
            res.user = User()
            res.user.avatar_url = input_json.get('avatarUrl')
            res.user.name = input_json.get('userName')
            res.user.user_id = input_json.get('userId')

        res.categories = input_json.get('categories', [])

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
        wkt = input_json.get('geometryWKT')
        if wkt:
            res.geometry = QgsGeometry.fromWkt(wkt)

        res.tile_url = input_json.get('tileUrl')
        file_size = input_json.get('filesize')
        if file_size is not None:
            res.file_size = int(file_size)

        updated_at_seconds = input_json.get('updatedAt')
        if updated_at_seconds is not None:
            res.updated_at = QDateTime.fromSecsSinceEpoch(int(updated_at_seconds))

        res.domain_name = input_json.get('domainName')

        tile_url_expiry = input_json.get('tileUrlExpiryAt')
        if tile_url_expiry is not None:
            res.tile_url_expiry_at = QDateTime.fromSecsSinceEpoch(int(tile_url_expiry))

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
        # default to filtering to tile layers only
        self.listing_type: Optional[
            ListingType] = listing_type if listing_type is not None else ListingType.TileLayer
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
            # seems SOAR api is sensitive to WKT format! This must be uppercase
            params['aoi'] = self.aoi.asWkt(4).upper()
        return params


class ApiClient(QObject):
    """
    API client for soar.earth API
    """

    URL = "https://api.soar.earth/v1"
    LISTINGS_ENDPOINT = 'listings'
    LOGIN_ENDPOINT = 'user/login'
    UPLOAD_ENDPOINT = 'listings/upload'

    error_occurred = pyqtSignal(str)
    login_error_occurred = pyqtSignal(str)
    fetched_token = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # standard headers to add to all requests
        self.headers = {
            'Subdomain': 'soar.earth',
            'accept': 'application/json'
        }

        self.login_reply: Optional[QNetworkReply] = None

    def login(self, username: str, password: str, domain: str = 'soar.earth'):
        """
        Logins and authorizes a user
        """
        if self.login_reply:
            return

        headers = {
            'Content-Type': 'application/json'
        }
        if domain:
            headers['Subdomain'] = domain

        params = {
            'email': username,
            'password': password
        }
        login_request = self._build_request(self.LOGIN_ENDPOINT, headers)

        self.login_reply = QgsNetworkAccessManager.instance().post(login_request,
                                                                   json.dumps(params).encode())
        self.login_reply.finished.connect(self._login_finished)

    def _login_finished(self):
        if sip.isdeleted(self):
            return []

        if not self.login_reply or sip.isdeleted(self.login_reply):
            self.login_reply = None
            return

        reply = self.login_reply
        self.login_reply = None

        if reply.error() == QNetworkReply.OperationCanceledError:
            self.login_error_occurred.emit('Login canceled')
            return

        if reply.error() != QNetworkReply.NoError:
            reply_json = json.loads(reply.readAll().data().decode())

            error = reply_json.get('error')
            if not error:
                error = reply.errorString()

            self.login_error_occurred.emit(error)
            return

        reply_json = json.loads(reply.readAll().data().decode())
        self.id_token = reply_json['idToken']
        self.fetched_token.emit()

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

    def request_listing(self,
                        listing_id: int,
                        domain: str = 'soar.earth', ) -> QNetworkRequest:
        """
        Creates a listing request
        """
        headers = {}
        if domain:
            headers = {
                'Subdomain': domain
            }
        network_request = self._build_request(f'{self.LISTINGS_ENDPOINT}/{listing_id}',
                                              headers)

        return network_request

    def parse_listings_reply(self, reply: QNetworkReply) -> List[Listing]:
        """
        Parse a listings reply and return as a list of Listings objects
        """
        if sip.isdeleted(self):
            return []

        if reply.error() == QNetworkReply.OperationCanceledError:
            return []

        if reply.error() != QNetworkReply.NoError:
            self.error_occurred.emit(reply.errorString())
            return []

        listings_json = json.loads(reply.readAll().data().decode())['listings']
        return [Listing.from_json(listing) for listing in listings_json]

    def parse_listing_reply(self, reply: QNetworkReply) -> Optional[Listing]:
        """
        Parse a listing reply and return as a fully-populated Listing object
        """
        if sip.isdeleted(self):
            return None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return None

        if reply.error() != QNetworkReply.NoError:
            self.error_occurred.emit(reply.errorString())
            return None

        listing_json = json.loads(reply.readAll().data().decode())
        return Listing.from_json(listing_json)

    def request_upload_start(self,
                             export_settings: MapExportSettings,
                             domain: str = 'soar.earth') -> QNetworkReply:
        """
        Asks for a upload
        """
        headers = {}
        if domain:
            headers = {
                'Subdomain': domain,
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(self.id_token)
            }

        metadata = {
            'title': export_settings.title,
            'description': export_settings.description,
            'tags': export_settings.tags,
            'categories': [export_settings.category],
        }

        params = {
            'listingType': 'TILE_LAYER',
            'filename': Path(export_settings.output_file_name).name,
            'metadata': json.dumps(metadata),
            'title': metadata['title'],
            'description': metadata['description'],
            'tags': metadata['tags'],
            'categories': metadata['categories']
        }

        request = self._build_request(self.UPLOAD_ENDPOINT,
                                      headers)

        return QgsNetworkAccessManager.instance().post(request, json.dumps(params).encode())

    def parse_request_upload_reply(self,
                                   reply: QNetworkReply) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Parses a request upload reply
        """
        if sip.isdeleted(self):
            return None, None

        if not reply or sip.isdeleted(reply):
            return None, None

        if reply.error() == QNetworkReply.OperationCanceledError:
            return None, None

        if reply.error() != QNetworkReply.NoError:
            reply_json = json.loads(reply.readAll().data().decode())

            error = reply_json.get('error')
            if not error:
                error = reply.errorString()

            return None, error

        return json.loads(reply.readAll().data().decode()), None

    def upload_file(self, file_path: str, upload_details: Dict):
        """
        Uploads a file
        """
        from .uploader import SoarUploader

        SoarUploader.upload_file(
            file_path,
            bucket_name=upload_details['bucketName'],
            filename=upload_details['filename'],
            access_key_id=upload_details['stsCredentials']['accessKeyId'],
            security_token=upload_details['stsCredentials']['securityToken'],
            access_secret_key=upload_details['stsCredentials']['accessSecretKey'],
            listing_id=upload_details['listingId'],
            key=upload_details['key'],
            oss_region=upload_details['ossRegion']
        )

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


API_CLIENT = ApiClient()
