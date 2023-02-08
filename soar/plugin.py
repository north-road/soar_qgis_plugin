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
from qgis.core import (
    QgsProviderRegistry,
    QgsProject,
    QgsMessageOutput
)
from qgis.gui import (
    QgsGui,
    QgsSourceSelectProvider,
    QgisInterface
)

from .gui import (
    GuiUtils,
    MapExportDialog
)
from .gui.browser_dock_widget import BrowserDockWidget
from .gui.data_source_widget import SoarDataSourceWidget
from .core import (
    ProjectManager,
    MapValidator
)


class SoarSourceSelectProvider(QgsSourceSelectProvider):
    """
    Data source manager widget provider for soar.earth datasets
    """

    # QgsSourceSelectProvider interface
    # pylint: disable=missing-function-docstring,unused-argument

    def providerKey(self):
        return 'soar.earth'

    def text(self):
        return SoarPlugin.tr('Soar.earth')

    def toolTip(self):
        return SoarPlugin.tr('Browse and search Soar.earth data')

    def icon(self):
        return GuiUtils.get_icon('soar_logo.svg')

    def createDataSourceWidget(self,
                               parent=None,
                               fl=Qt.Widget,
                               widgetMode=QgsProviderRegistry.WidgetMode.Embedded):
        return SoarDataSourceWidget()

    # pylint: enable=missing-function-docstring,unused-argument


class SoarPlugin:
    """
    Soar.earth plugin
    """

    def __init__(self, iface: QgisInterface):
        self.iface: QgisInterface = iface

        self.dock: Optional[BrowserDockWidget] = None
        self.browse_action: Optional[QAction] = None
        self.export_map_action: Optional[QAction] = None

        self.source_select_provider: Optional[SoarSourceSelectProvider] = None
        self.project_manager = ProjectManager(QgsProject.instance())
        self.map_dialog = None

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

        self.export_map_action = QAction(self.tr("Export Map to Soar.earth"), self.iface.mainWindow())
        self.export_map_action.setIcon(GuiUtils.get_icon('listing_search.svg'))
        self.export_map_action.setToolTip(self.tr('Exports the current map to Soar.earth'))
        self.export_map_action.triggered.connect(self.export_map_to_soar)
        try:
            self.iface.addProjectExportAction(self.export_map_action)
        except AttributeError:
            # addProjectExportAction was added in QGIS 3.30
            import_export_menu = GuiUtils.get_project_import_export_menu()
            if import_export_menu:
                # find nice insertion point
                export_separator = [a for a in import_export_menu.actions() if a.isSeparator()]
                if export_separator:
                    import_export_menu.insertAction(export_separator[0], self.export_map_action)
                else:
                    import_export_menu.addAction(self.export_map_action)

        self.source_select_provider = SoarSourceSelectProvider()
        QgsGui.sourceSelectProviderRegistry().addProvider(self.source_select_provider)

        self.dock.hide()

    def unload(self):
        if self.map_dialog and not sip.isdeleted(self.map_dialog):
            self.map_dialog.deleteLater()
        self.map_dialog = None

        if not sip.isdeleted(self.dock):
            self.dock.cancel_active_requests()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        self.dock = None

        for action in (self.browse_action, self.export_map_action):
            if not sip.isdeleted(action):
                action.deleteLater()
        self.browse_action = None
        self.export_map_action = None

        if self.source_select_provider and not sip.isdeleted(self.source_select_provider):
            QgsGui.sourceSelectProviderRegistry().removeProvider(self.source_select_provider)
        self.source_select_provider = None

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

    def export_map_to_soar(self):
        """
        Exports the current map (project) to soar
        """
        if self.map_dialog and not sip.isdeleted(self.map_dialog):
            self.map_dialog.show()
            return

        validator = MapValidator(QgsProject.instance())
        if not validator.validate():

            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(self.tr('Export Map to Soar.earth'))
            dialog.setMessage(validator.error_message(), QgsMessageOutput.MessageHtml)
            dialog.showMessage()
            return

        self.map_dialog = MapExportDialog(self.iface.mapCanvas(), self.project_manager)

        def dialog_rejected():
            if not sip.isdeleted(self.map_dialog):
                self.map_dialog.deleteLater()
            self.map_dialog = None

        self.map_dialog.rejected.connect(dialog_rejected)
        self.map_dialog.show()