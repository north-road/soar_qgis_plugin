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

from enum import Enum

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject,
    pyqtSignal
)
from qgis.PyQt.QtWidgets import (
    QPushButton
)

from qgis.core import (
    Qgis,
    QgsSettings
)
from qgis.gui import (
    QgsMessageBarItem
)
from qgis.utils import iface

from ..core import API_CLIENT


class LoginStatus(Enum):
    """
    Login statuses
    """
    LoggedOut = 0
    LoggingIn = 1
    LoggedIn = 2


class LoginManager(QObject):
    """
    Handles the GUI component of user login state
    """

    logged_in = pyqtSignal()
    login_failed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.status: LoginStatus = LoginStatus.LoggedOut

        self.username: str = QgsSettings().value('soar/username', '', str)
        self.password: str = ''

        self._logging_in_message = None
        self._login_failed_message = None

        API_CLIENT.login_error_occurred.connect(self._login_error_occurred)
        API_CLIENT.fetched_token.connect(self._login_success)

        self.queued_callbacks = []

    def is_logged_in(self) -> bool:
        """
        Returns True if the user is logged in
        """
        return self.status == LoginStatus.LoggedIn

    def login_callback(self, callback) -> bool:
        """
        Returns True if the user is already logged in, or False
        if a login is in progress and the operation needs to wait
        for the logged_in signal before proceeding
        """
        if self.status == LoginStatus.LoggedIn:
            callback()
            return True

        self.queued_callbacks.append(callback)
        return self.start_login()

    def start_login(self):
        """
        Start a login process
        """
        if self.status != LoginStatus.LoggedOut:
            return False

        self._cleanup_messages()

        from .credential_dialog import CredentialDialog  # pylint: disable=import-outside-toplevel
        dlg = CredentialDialog()
        if not dlg.exec_():
            return False

        self.status = LoginStatus.LoggingIn

        username = dlg.username()
        password = dlg.password()

        self._logging_in_message = QgsMessageBarItem(self.tr('Soar'),
                                                     self.tr('Logging in...'),
                                                     Qgis.MessageLevel.Info)
        iface.messageBar().pushItem(self._logging_in_message)

        API_CLIENT.login(username, password)
        return False

    def _cleanup_messages(self):
        """
        Removes outdated message bar items
        """
        if self._logging_in_message and not sip.isdeleted(self._logging_in_message):
            iface.messageBar().popWidget(self._logging_in_message)
            self._logging_in_message = None
        if self._login_failed_message and not sip.isdeleted(self._login_failed_message):
            iface.messageBar().popWidget(self._login_failed_message)
            self._login_failed_message = None

    def _login_error_occurred(self, error: str):
        """
        Triggered when a login error occurs
        """
        self._cleanup_messages()

        self.status = LoginStatus.LoggedOut
        login_error = self.tr('Login error: {}'.format(error))

        self._login_failed_message = QgsMessageBarItem(self.tr('Soar'),
                                                       login_error,
                                                       Qgis.MessageLevel.Critical)

        login_button = QPushButton(self.tr("Try Again"))
        login_button.clicked.connect(self.start_login)
        self._login_failed_message.layout().addWidget(login_button)

        iface.messageBar().pushItem(self._login_failed_message)

        self.queued_callbacks = []
        self.login_failed.emit()

    def _login_success(self):
        """
        Triggered when a login succeeds
        """
        self._cleanup_messages()

        self.status = LoginStatus.LoggedIn
        iface.messageBar().pushSuccess(self.tr('Soar'), self.tr('Logged in'))

        callbacks = self.queued_callbacks
        self.queued_callbacks = []
        for callback in callbacks:
            callback()

        self.logged_in.emit()


LOGIN_MANAGER = LoginManager()
