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

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialogButtonBox
)

from .gui_utils import GuiUtils

ui, base = uic.loadUiType(GuiUtils.get_ui_file_path('confirm_export_dialog.ui'))


class ConfirmExportDialog(base, ui):
    """
    A dialog for confirming uploads to soar.earth
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)

        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr('Publish'))

        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.check_accept.toggled.connect(self._toggle_accept)

        self.setWindowTitle(self.tr('Export Map to Soar.earth'))

    def _toggle_accept(self, accepted: bool):
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(accepted)
