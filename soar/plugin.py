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

from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt,
    QCoreApplication,
    QEvent
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QPushButton
)
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsProviderRegistry,
    QgsProject,
    QgsMessageOutput
)
from qgis.gui import (
    QgsGui,
    QgsSourceSelectProvider,
    QgisInterface
)

from .core import (
    ProjectManager,
    MapValidator,
    MapPublisher,
    SoarEarthProvider
)
from .gui import (
    GuiUtils,
    MapExportDialog,
    ConfirmExportDialog
)
from .gui import (
    LOGIN_MANAGER
)
from .gui.browser_dock_widget import BrowserDockWidget
from .gui.data_source_widget import SoarDataSourceWidget


class SoarSourceSelectProvider(QgsSourceSelectProvider):
    """
    Data source manager widget provider for soar.earth datasets
    """

    # QgsSourceSelectProvider interface
    # pylint: disable=missing-function-docstring,unused-argument

    def providerKey(self):
        return 'soar'

    def text(self):
        return SoarPlugin.tr('Soar')

    def toolTip(self):
        return SoarPlugin.tr('Browse and search Soar data')

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
    Soar plugin
    """

    def __init__(self, iface: QgisInterface):
        self.iface: QgisInterface = iface

        self.dock: Optional[BrowserDockWidget] = None
        self.browse_action: Optional[QAction] = None
        self.export_map_action: Optional[QAction] = None

        self.source_select_provider: Optional[SoarSourceSelectProvider] = None
        self.project_manager = ProjectManager(QgsProject.instance())
        self.map_dialog: Optional[MapExportDialog] = None

        self.provider = SoarEarthProvider()

        self.task = None

        # qgis plugin interface

    # pylint: disable=missing-function-docstring

    def initGui(self):
        self.initProcessing()

        self.dock = BrowserDockWidget()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.browse_action = QAction(self.tr("Show Soar Browser"), self.iface.mainWindow())
        self.browse_action.setIcon(GuiUtils.get_icon('listing_search.svg'))
        self.browse_action.setCheckable(True)
        self.browse_action.setToolTip(self.tr('Browse and search Soar data'))
        self.dock.setToggleVisibilityAction(self.browse_action)

        self.iface.pluginToolBar().addAction(self.browse_action)

        self.export_map_action = QAction(self.tr("Export Map to Soar"),
                                         self.iface.mainWindow())
        self.export_map_action.setIcon(GuiUtils.get_icon('soar_export.svg'))
        self.export_map_action.setToolTip(self.tr('Exports the current map to Soar'))
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

    def initProcessing(self):
        """Create the Processing provider"""
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.provider = None

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
        LOGIN_MANAGER.login_callback(self._export_map_to_soar_private)

    def _export_map_to_soar_private(self):
        """
        Exports the current map (project) to soar
        """
        if self.map_dialog and not sip.isdeleted(self.map_dialog):
            self.map_dialog.show()
            return

        validator = MapValidator(QgsProject.instance())
        if not validator.validate():
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(self.tr('Export Map to Soar'))
            dialog.setMessage(validator.error_message(), QgsMessageOutput.MessageHtml)
            dialog.showMessage()
            return

        self.map_dialog = MapExportDialog(self.iface.mapCanvas(), self.project_manager)

        def dialog_rejected():
            if not sip.isdeleted(self.map_dialog):
                self.map_dialog.deleteLater()
            self.map_dialog = None

        def dialog_accepted():
            settings = self.map_dialog.export_settings()

            if not sip.isdeleted(self.map_dialog):
                self.map_dialog.deleteLater()
            self.map_dialog = None

            confirm_dialog = ConfirmExportDialog()
            if not confirm_dialog.exec():
                return

            self.task = MapPublisher(settings, self.iface.mapCanvas())
            self.task.success.connect(self._upload_success)
            self.task.failed.connect(self._upload_failed)

            QgsApplication.taskManager().addTask(self.task)

        self.map_dialog.rejected.connect(dialog_rejected)
        self.map_dialog.accepted.connect(dialog_accepted)
        self.map_dialog.show()

    def _upload_success(self):
        """
        Triggered on a successful upload
        """

        extended_message = self.tr('<p>Once your content has been approved by a moderator, you can '
                                   'view it in your dashboard. Simply go to your dashboard, and '
                                   'select ‘My Imagery’. You’ll see all of your uploaded maps, '
                                   'including rejected items.</p>'
                                   '<p>If your image is rejected, it’ll be returned with moderator '
                                   'feedback to explain  why it wasn’t posted. If this happens, '
                                   'simply click on the 3 dots in the top right '
                                   'corner and select delete. Once you’ve made any necessary '
                                   'modifications, you can re-upload.</p>')

        self.show_extended_message(self.tr('Map successful published'),
                                   self.tr('Map Published to Soar'),
                                   extended_message, level=Qgis.Success,
                                   button_text=self.tr("What's Next?"))

    def _upload_failed(self, error: str):
        """
        Triggered on a failed upload
        """
        error_message = self.tr('<p>The upload to Soar failed.</p>'
                                '<p>The following error was raised:</p>'
                                '<code>{}</code>'.format(error))

        self.show_extended_message(self.tr('Upload failed'),
                                   self.tr('Soar Upload Failed'),
                                   error_message,
                                   level=Qgis.Critical)

    def show_extended_message(self, short_message, title, long_message, level=Qgis.Warning,
                              button_text=None):
        """
        Shows a warning via the QGIS message bar
        """

        def show_details(_):
            dialog = QgsMessageOutput.createMessageOutput()
            dialog.setTitle(title)
            dialog.setMessage(long_message, QgsMessageOutput.MessageHtml)
            dialog.showMessage()

        message_widget = self.iface.messageBar().createMessage(self.tr('Soar'),
                                                               short_message)
        if button_text is None:
            button_text = self.tr("Details")
        details_button = QPushButton(button_text)
        details_button.clicked.connect(show_details)
        message_widget.layout().addWidget(details_button)
        self.iface.messageBar().pushWidget(message_widget, level, 0)
