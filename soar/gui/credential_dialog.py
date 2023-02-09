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
from qgis.core import QgsSettings

from .gui_utils import GuiUtils

ui, base = uic.loadUiType(GuiUtils.get_ui_file_path('credential_dialog.ui'))


class CredentialDialog(base, ui):
    """
    A dialog for soar.earth credentials
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.leUsername.setText(QgsSettings().value('soar/username', '', str))

        self.leUsername.textChanged.connect(self._validate)
        self.lePassword.textChanged.connect(self._validate)

        self.leUsername.setFocus()

        self._validate()

    def _validate(self):
        is_valid = bool(self.username() and self.password())

        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(is_valid)

    def accept(self):
        QgsSettings().setValue('soar/username', self.username())

        super().accept()

    def username(self) -> str:
        return self.leUsername.text()

    def password(self) -> str:
        return self.lePassword.text()
