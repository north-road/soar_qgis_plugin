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

from typing import Tuple

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    QSize
)
from qgis.core import (
    QgsScaleCalculator
)
from qgis.gui import (
    QgsMapCanvas,
    QgsExtentGroupBox,
    QgsScaleWidget,
    QgsSpinBox,
    QgsRatioLockButton
)

from .gui_utils import GuiUtils
from ..core import (
    ProjectManager,
    MapExportSettings
)

ui, base = uic.loadUiType(GuiUtils.get_ui_file_path('map_export_dialog.ui'))


class MapExportDialog(base, ui):
    """
    A dialog for entering properties of a export to soar.earth
    """

    def __init__(self,  # pylint: disable=too-many-statements
                 map_canvas: QgsMapCanvas,
                 project_manager: ProjectManager,
                 parent=None):
        super().__init__(parent)

        self.setupUi(self)

        self.setWindowTitle(self.tr('Export Map to Soar'))

        self.map_canvas = map_canvas
        self.project_manager = project_manager

        map_settings = self.map_canvas.mapSettings()
        self.extent = self.project_manager.export_extent()
        if not self.extent:
            self.extent = map_settings.visibleExtent()

        self.dpi = 96
        self.size = self.project_manager.export_size()
        if self.size.isEmpty():
            self.size = map_settings.outputSize()

        self.map_title_edit.setText(self.project_manager.soar_map_title())
        self.description_edit.setPlainText(self.project_manager.soar_map_description())
        self.tags_edit.setText(';'.join(self.project_manager.soar_map_tags()))

        category_index = 1
        for combo in (self.category_combo,
                      self.category_combo_2,
                      self.category_combo_3):
            combo.addItem('')
            combo.addItem(self.tr('Agriculture'), 'agriculture')
            combo.addItem(self.tr('Climate'), 'climate')
            combo.addItem(self.tr('Earth Art'), 'earth-art')
            combo.addItem(self.tr('Economic'), 'economic')
            combo.addItem(self.tr('Geology'), 'geology')
            combo.addItem(self.tr('History'), 'history')
            combo.addItem(self.tr('Marine'), 'marine')
            combo.addItem(self.tr('Political'), 'political')
            combo.addItem(self.tr('Terrain'), 'terrain')
            combo.addItem(self.tr('Transport'), 'transport')
            combo.addItem(self.tr('Urban'), 'urban')
            combo.currentIndexChanged.connect(self._category_combo_changed)

            project_category = self.project_manager.soar_category(
                category_index
            )
            print(project_category)
            if project_category:
                combo.setCurrentIndex(
                    combo.findData(project_category)
                )
            else:
                combo.setCurrentIndex(0)

            category_index += 1

        self._category_combo_changed()

        # some type hints:
        self.mExtentGroupBox: QgsExtentGroupBox
        self.mScaleWidget: QgsScaleWidget
        self.mOutputWidthSpinBox: QgsSpinBox
        self.mOutputHeightSpinBox: QgsSpinBox
        self.mLockAspectRatio: QgsRatioLockButton

        self.mExtentGroupBox.setOutputCrs(map_settings.destinationCrs())
        self.mExtentGroupBox.setCurrentExtent(self.extent, map_settings.destinationCrs())
        self.mExtentGroupBox.setOutputExtentFromCurrent()
        self.mExtentGroupBox.setMapCanvas(self.map_canvas)

        scale = self.project_manager.export_scale()
        if not scale:
            scale = map_settings.scale()
        self.mScaleWidget.setScale(scale)
        self.mScaleWidget.setMapCanvas(self.map_canvas)
        self.mScaleWidget.setShowCurrentScaleButton(True)

        self.mOutputWidthSpinBox.editingFinished.connect(self.update_output_width)
        self.mOutputHeightSpinBox.editingFinished.connect(self.update_output_height)
        self.mExtentGroupBox.extentChanged.connect(self.update_extent)
        self.mScaleWidget.scaleChanged.connect(self.update_scale)
        self.mLockAspectRatio.lockChanged.connect(self.lock_changed)

        self.mLockAspectRatio.setLocked(True)

        self.update_output_size()

    def _category_combo_changed(self):
        """
        Called when a category combo value is changed
        """
        category_1_exists = bool(self.category_combo.currentData())

        if not category_1_exists and self.category_combo_2.currentData():
            self.category_combo.setCurrentIndex(
                self.category_combo_2.currentIndex())
            self.category_combo_2.setCurrentIndex(0)
            category_1_exists = True

        category_2_exists = category_1_exists and \
            bool(self.category_combo_2.currentData())

        if not category_2_exists and self.category_combo_3.currentData():
            self.category_combo_2.setCurrentIndex(
                self.category_combo_3.currentIndex())
            self.category_combo_3.setCurrentIndex(0)
            category_2_exists = True

        self.category_combo_2.setVisible(category_1_exists)
        self.category_combo_3.setVisible(category_2_exists)

    def update_output_width(self):
        """
        Updates the dialog state when output width changes
        """
        width = self.mOutputWidthSpinBox.value()

        scale = width / self.size.width()
        adjustment = ((self.extent.width() * scale) - self.extent.width()) / 2
        self.size.setWidth(width)

        self.extent.setXMinimum(self.extent.xMinimum() - adjustment)
        self.extent.setXMaximum(self.extent.xMaximum() + adjustment)

        if self.mLockAspectRatio.locked():
            height = width * self.mExtentGroupBox.ratio().height() / self.mExtentGroupBox.ratio().width()
            scale = height / self.size.height()
            adjustment = ((self.extent.height() * scale) - self.extent.height()) / 2

            self.mOutputHeightSpinBox.blockSignals(True)
            self.mOutputHeightSpinBox.setValue(int(round(height)))
            self.mOutputHeightSpinBox.blockSignals(False)

            self.size.setHeight(int(round(height)))

            self.extent.setYMinimum(self.extent.yMinimum() - adjustment)
            self.extent.setYMaximum(self.extent.yMaximum() + adjustment)

        self.mExtentGroupBox.blockSignals(True)
        self.mExtentGroupBox.setOutputExtentFromUser(self.extent,
                                                     self.mExtentGroupBox.currentCrs())
        self.mExtentGroupBox.blockSignals(False)

    def update_output_height(self):
        """
        Updates the dialog state when output height changes
        """
        height = self.mOutputHeightSpinBox.value()

        scale = height / self.size.height()
        adjustment = ((self.extent.height() * scale) - self.extent.height()) / 2
        self.size.setHeight(height)

        self.extent.setYMinimum(self.extent.yMinimum() - adjustment)
        self.extent.setYMaximum(self.extent.yMaximum() + adjustment)

        if self.mLockAspectRatio.locked():
            width = height * self.mExtentGroupBox.ratio().width() / self.mExtentGroupBox.ratio().height()
            scale = width / self.size.width()
            adjustment = ((self.extent.width() * scale) - self.extent.width()) / 2

            self.mOutputWidthSpinBox.blockSignals(True)
            self.mOutputWidthSpinBox.setValue(int(round(width)))
            self.mOutputWidthSpinBox.blockSignals(False)

            self.size.setWidth(int(round(width)))

            self.extent.setXMinimum(self.extent.xMinimum() - adjustment)
            self.extent.setXMaximum(self.extent.xMaximum() + adjustment)

        self.mExtentGroupBox.blockSignals(True)
        self.mExtentGroupBox.setOutputExtentFromUser(self.extent,
                                                     self.mExtentGroupBox.currentCrs())
        self.mExtentGroupBox.blockSignals(False)

    def update_extent(self, extent):
        """
        Updates the extent calculation
        """
        if self.mExtentGroupBox.extentState() != QgsExtentGroupBox.UserExtent:
            current_dpi = self.dpi

            ms = self.map_canvas.mapSettings()
            ms.setRotation(0)
            self.dpi = round(ms.outputDpi())
            self.size.setWidth(
                int(round(ms.outputSize().width() * extent.width() / ms.visibleExtent().width())))
            self.size.setHeight(int(round(
                ms.outputSize().height() * extent.height() / ms.visibleExtent().height())))

            self.mScaleWidget.blockSignals(True)
            self.mScaleWidget.setScale(ms.scale())
            self.mScaleWidget.blockSignals(False)

            if current_dpi != self.dpi:
                self.update_dpi(current_dpi)
        else:
            self.size.setWidth(
                int(round(self.size.width() * extent.width() / self.extent.width())))
            self.size.setHeight(
                int(round(self.size.height() * extent.height() / self.extent.height())))

        self.update_output_size()

        self.extent = extent
        if self.mLockAspectRatio.locked():
            self.mExtentGroupBox.setRatio(QSize(self.size.width(), self.size.height()))

    def update_dpi(self, dpi):
        """
        Updates the dialog state when output dpi changes
        """
        self.size = QSize(int(round(self.size.width() * dpi / self.dpi)),
                          int(round(self.size.height() * dpi / self.dpi)))
        self.dpi = dpi
        self.update_output_size()

    def update_scale(self, scale):
        """
        Updates the dialog state when output scale changes
        """
        calculator = QgsScaleCalculator()
        calculator.setMapUnits(self.mExtentGroupBox.currentCrs().mapUnits())
        calculator.setDpi(self.dpi)

        old_scale = calculator.calculate(self.extent, self.size.width())
        scale_ratio = scale / old_scale

        self.extent.scale(scale_ratio)
        self.mExtentGroupBox.setOutputExtentFromUser(self.extent,
                                                     self.mExtentGroupBox.currentCrs())

    def lock_changed(self, locked: bool):
        """
        Updates the dialog state when ratio lock is changed
        """
        if locked:
            self.mExtentGroupBox.setRatio(
                QSize(self.mOutputWidthSpinBox.value(), self.mOutputHeightSpinBox.value()))
        else:
            self.mExtentGroupBox.setRatio(QSize(0, 0))

    def update_output_size(self):
        """
        Updates the size shown in the dialog
        """
        self.mOutputWidthSpinBox.blockSignals(True)
        self.mOutputWidthSpinBox.setValue(self.size.width())
        self.mOutputWidthSpinBox.blockSignals(False)

        self.mOutputHeightSpinBox.blockSignals(True)
        self.mOutputHeightSpinBox.setValue(self.size.height())
        self.mOutputHeightSpinBox.blockSignals(False)

    def validate(self) -> Tuple[bool, str]:
        """
        Validates the dialog settings
        """
        title = self.map_title_edit.text()
        if not title:
            return False, self.tr('A map title must be entered')

        description = self.description_edit.toPlainText()
        if not description:
            return False, self.tr('A map description must be entered')

        tags = self.tags_edit.text()
        if not tags:
            return False, self.tr('Map tags must be entered')

        category = self.category_combo.currentData()
        if not category:
            return False, self.tr('A category must be selected')

        return True, ''

    def export_settings(self) -> MapExportSettings:
        """
        Returns the export settings defined in the dialog
        """
        export_settings = MapExportSettings()

        export_settings.title = self.map_title_edit.text()
        export_settings.description = self.description_edit.toPlainText()
        export_settings.tags = self.tags_edit.text().split(';')
        export_settings.categories = [cat for cat in (
            self.category_combo.currentData(),
            self.category_combo_2.currentData(),
            self.category_combo_3.currentData(),
        ) if cat]
        export_settings.size = QSize(self.mOutputWidthSpinBox.value(), self.mOutputHeightSpinBox.value())
        export_settings.scale = self.mScaleWidget.scale()
        export_settings.extent = self.mExtentGroupBox.outputExtent()

        return export_settings

    def save_settings(self):
        """
        Saves the dialog's settings
        """
        export_settings = self.export_settings()

        self.project_manager.set_soar_map_title(export_settings.title)
        self.project_manager.set_soar_map_description(export_settings.description)
        self.project_manager.set_soar_map_tags(export_settings.tags)
        for idx, category in enumerate(export_settings.categories):
            self.project_manager.set_soar_category(category,
                                                   idx + 1)
        self.project_manager.set_export_size(export_settings.size)
        self.project_manager.set_export_scale(export_settings.scale)
        self.project_manager.set_export_extent(export_settings.extent)

    def accept(self):  # pylint: disable=missing-function-docstring
        self.message_bar.clearWidgets()

        res, error = self.validate()
        if not res:
            self.message_bar.pushWarning('', error)
            return

        self.save_settings()

        super().accept()
