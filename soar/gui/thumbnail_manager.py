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


from collections import defaultdict
from functools import partial

from qgis.PyQt import sip
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QImage
from qgis.PyQt.QtWidgets import QWidget

from qgis.core import QgsNetworkAccessManager


class ThumbnailManager:
    """
    Handles download, caching and display of thumbnails
    """

    def __init__(self):
        self.cache = {}
        self.widgets = defaultdict(list)
        self.queued_replies = set()

    def download(self, url: str, widget: QWidget):
        """
        Downloads a thumbnail from a url and applies it to a widget on completion
        """
        if url in self.cache:
            widget.set_thumbnail(self.cache[url])
        else:
            self.widgets[url].append(widget)
            reply = QgsNetworkAccessManager.instance().get(QNetworkRequest(QUrl(url)))
            self.queued_replies.add(reply)
            if reply.isFinished():
                self.thumbnail_downloaded(reply)
            else:
                reply.finished.connect(partial(self.thumbnail_downloaded, reply))

    def thumbnail_downloaded(self, reply):
        """
        Called when a thumbnail has been fetched
        """
        self.queued_replies.remove(reply)
        if reply.error() == QNetworkReply.NoError:
            url = reply.url().toString()
            img = QImage()
            img.loadFromData(reply.readAll())
            self.cache[url] = img
            for w in self.widgets[url]:
                # the widget might have been deleted
                if not sip.isdeleted(w):
                    w.set_thumbnail(img)

            del self.widgets[url]


THUMBNAIL_MANAGER_INSTANCE = ThumbnailManager()


def download_thumbnail(url, widget):
    """
    Downloads a thumbnail and automatically applies it to a widget when fetched
    """
    THUMBNAIL_MANAGER_INSTANCE.download(url, widget)
