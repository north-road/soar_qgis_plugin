from enum import Enum

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject,
    pyqtSignal
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

    def _cleanup_messages(self):
        if self._logging_in_message and not sip.isdeleted(self._logging_in_message):
            iface.messageBar().popWidget(self._logging_in_message)
            self._logging_in_message = None
        if self._login_failed_message and not sip.isdeleted(self._login_failed_message):
            iface.messageBar().popWidget(self._login_failed_message)
            self._login_failed_message = None

    def _login_error_occurred(self, error: str):
        self._cleanup_messages()

        self.status = LoginStatus.LoggedOut
        login_error = self.tr('Login error: {}'.format(error))

        self._login_failed_message = QgsMessageBarItem(self.tr('Soar.earth'),
                                                     login_error,
                                                     Qgis.MessageLevel.Critical)
        iface.messageBar().pushItem(self._login_failed_message)

        self.queued_callbacks = []
        self.login_failed.emit()

    def _login_success(self):
        self._cleanup_messages()

        self.status = LoginStatus.LoggedIn
        iface.messageBar().pushSuccess(self.tr('Soar.earth'), self.tr('Logged in'))

        callbacks = self.queued_callbacks
        self.queued_callbacks = []
        for callback in callbacks:
            callback()

        self.logged_in.emit()


LOGIN_MANAGER = LoginManager()
