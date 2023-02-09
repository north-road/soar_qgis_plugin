from enum import Enum

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject,
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
    LoggedOut = 0
    LoggingIn = 1
    LoggedIn = 2


class LoginManager(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.status: LoginStatus = LoginStatus.LoggedOut

        self.username: str = QgsSettings().value('soar/username', '', str)
        self.password: str = ''

        self._logging_in_message = None

        API_CLIENT.login_error_occurred.connect(self._login_error_occurred)
        API_CLIENT.fetched_token.connect(self._login_success)

        self.queued_callbacks = []

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

        if self.status == LoginStatus.LoggingIn:
            return False

        from .credential_dialog import CredentialDialog
        dlg = CredentialDialog()
        if not dlg.exec_():
            return False

        self.status = LoginStatus.LoggingIn

        username = dlg.username()
        password = dlg.password()

        self._logging_in_message = QgsMessageBarItem(self.tr('Soar.earth'),
                                                     self.tr('Logging in...'),
                                                     Qgis.MessageLevel.Info)
        iface.messageBar().pushItem(self._logging_in_message)

        API_CLIENT.login(username, password)
        return False

    def _login_error_occurred(self, error: str):
        if self._logging_in_message and not sip.isdeleted(self._logging_in_message):
            iface.messageBar().popWidget(self._logging_in_message)
            self._logging_in_message = None

        self.status = LoginStatus.LoggedOut
        login_error = self.tr('Login error: {}'.format(error))
        iface.messageBar().pushCritical(self.tr('Soar.earth'), login_error)

        self.queued_callbacks = []

    def _login_success(self):
        if self._logging_in_message and not sip.isdeleted(self._logging_in_message):
            iface.messageBar().popWidget(self._logging_in_message)
            self._logging_in_message = None

        self.status = LoginStatus.LoggedIn
        iface.messageBar().pushSuccess(self.tr('Soar.earth'), self.tr('Logged in'))

        callbacks = self.queued_callbacks
        self.queued_callbacks = []
        for callback in callbacks:
            callback()


LOGIN_MANAGER = LoginManager()
