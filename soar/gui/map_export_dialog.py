from qgis.PyQt import uic
from .gui_utils import GuiUtils


ui, base = uic.loadUiType(GuiUtils.get_ui_file_path('map_export_dialog.ui'))

class MapExportDialog(base, ui):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)