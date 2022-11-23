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

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QCoreApplication,
    QEvent
)
from qgis.PyQt.QtWidgets import (
    QAction
)

from .gui import GuiUtils
from .gui.browser_dock_widget import BrowserDockWidget


class SoarPlugin:
    """
    Soar.earth plugin
    """

    def __init__(self, iface):
        self.iface = iface

        self.dock: Optional[BrowserDockWidget] = None
        self.browse_action: Optional[QAction] = None

    # qgis plugin interface

    # pylint: disable=missing-function-docstring

    def initGui(self):
        self.dock = BrowserDockWidget()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.browse_action = QAction(self.tr("Show Soar.earth Browser"), self.iface.mainWindow())
        self.browse_action.setIcon(GuiUtils.get_icon('listing_search.svg'))
        self.browse_action.setCheckable(True)
        self.browse_action.setToolTip(self.tr('Browse and search Soar.earth data'))
        self.dock.setToggleVisibilityAction(self.browse_action)

        self.iface.pluginToolBar().addAction(self.browse_action)

        self.dock.hide()

    def unload(self):
        if not sip.isdeleted(self.dock):
            self.dock.cancel_active_requests()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        self.dock = None

        if not sip.isdeleted(self.browse_action):
            self.browse_action.deleteLater()
        self.browse_action = None

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    # pylint: enable=missing-function-docstring

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Soar', message)
