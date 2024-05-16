# -*- coding: utf-8 -*-
"""Soar.earth API client

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

import tempfile
from pathlib import Path
from typing import List, Optional

from osgeo import gdal
from qgis.PyQt.QtCore import (
    QSize,
    QEventLoop,
    pyqtSignal
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.core import (
    Qgis,
    QgsProject,
    QgsRectangle,
    QgsMapSettings,
    QgsCoordinateReferenceSystem,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsMapRendererTask,
    QgsTask,
    QgsMapSettingsUtils,
    QgsMapDecoration
)
from qgis.gui import (
    QgsMapCanvas
)


class MapExportSettings:
    """
    Contains map export/publishing settings
    """

    def __init__(self):
        self.title: str = ''
        self.description: str = ''
        self.tags: List[str] = []
        self.categories: List[str] = []
        self.size: QSize = QSize()
        self.scale: float = 0
        self.extent: QgsRectangle = QgsRectangle()
        self.output_file_name: Optional[str] = None
        self.include_decorations = True
        self.decorations: List[QgsMapDecoration] = []

    def map_settings(self, map_canvas: QgsMapCanvas) -> QgsMapSettings:
        """
        Converts the settings to a QgsMapSettings object
        """
        ms = QgsMapSettings()
        ms.setFlag(QgsMapSettings.Flag.Antialiasing, True)
        try:
            ms.setFlag(QgsMapSettings.Flag.HighQualityImageTransforms, True)
        except AttributeError:
            pass
        ms.setFlag(QgsMapSettings.Flag.ForceVectorOutput, True)
        ms.setFlag(QgsMapSettings.Flag.DrawEditingInfo, False)
        ms.setFlag(QgsMapSettings.Flag.DrawSelection, False)
        ms.setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:3857'))

        ms.setExtent(self.extent)
        ms.setOutputSize(self.size)
        ms.setOutputDpi(96)
        ms.setBackgroundColor(map_canvas.canvasColor())
        ms.setRotation(map_canvas.rotation())
        ms.setEllipsoid(QgsProject.instance().ellipsoid())
        layers = map_canvas.layers()

        try:
            if not QgsProject.instance().mainAnnotationLayer().isEmpty():
                layers.insert(0, QgsProject.instance().mainAnnotationLayer())
        except AttributeError:
            pass

        ms.setLayers(layers)
        ms.setLabelingEngineSettings(map_canvas.mapSettings().labelingEngineSettings())
        ms.setTransformContext(QgsProject.instance().transformContext())
        ms.setPathResolver(QgsProject.instance().pathResolver())
        ms.setTemporalRange(map_canvas.mapSettings().temporalRange())
        ms.setIsTemporal(map_canvas.mapSettings().isTemporal())

        expression_context = QgsExpressionContext()
        expression_context.appendScope(QgsExpressionContextUtils.globalScope())
        expression_context.appendScope(
            QgsExpressionContextUtils.projectScope(QgsProject.instance()))
        expression_context.appendScope(QgsExpressionContextUtils.mapSettingsScope(ms))

        ms.setExpressionContext(expression_context)
        try:
            ms.setRendererUsage(Qgis.RendererUsage.Export)
        except AttributeError:
            pass

        return ms


class MapPublisher(QgsTask):
    """
    A background task for exporting maps and uploading to soar.earth
    """

    success = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self,
                 settings: MapExportSettings,
                 canvas: QgsMapCanvas):
        super().__init__('Publishing map to Soar', QgsTask.Flag.CanCancel)

        self.settings = settings
        self.map_settings = self.settings.map_settings(canvas)

        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        temp_path = Path(self.temp_dir.name)
        self.settings.output_file_name = (temp_path / 'qgis_map_export.tiff').as_posix()

        render_task = QgsMapRendererTask(self.map_settings, self.settings.output_file_name,
                               fileFormat='TIF')
        if settings.decorations:
            render_task.addDecorations(settings.decorations)
        self.addSubTask(
            render_task,
            subTaskDependency=QgsTask.SubTaskDependency.ParentDependsOnSubTask
        )

        self.upload_start_reply: Optional[QNetworkReply] = None

    def cleanup(self):
        """
        Cleanup temporary files following the export
        """
        self.temp_dir.cleanup()
        self.temp_dir = None

    def run(self) -> bool:  # pylint: disable=missing-function-docstring
        self.georeference_output()

        from .client import API_CLIENT  # pylint: disable=import-outside-toplevel

        self.upload_start_reply = API_CLIENT.request_upload_start(self.settings)

        loop = QEventLoop()
        self.upload_start_reply.finished.connect(loop.quit)
        loop.exec()

        res, error = API_CLIENT.parse_request_upload_reply(self.upload_start_reply)
        self.upload_start_reply = None

        if res is None:
            # error occurred
            if error:
                self.failed.emit(error)

            self.cleanup()
            return False

        try:
            API_CLIENT.upload_file(self.settings.output_file_name, res)
            self.success.emit()
        except Exception as e:  # pylint: disable=broad-except
            self.failed.emit(str(e))

        self.cleanup()
        return True

    def georeference_output(self):
        """
        Applies georeferencing to the output image
        """
        a, b, c, d, e, f = QgsMapSettingsUtils.worldFileParameters(self.map_settings)
        c -= 0.5 * a
        c -= 0.5 * b
        f -= 0.5 * d
        f -= 0.5 * e

        dst_ds = gdal.Open(self.settings.output_file_name, gdal.GA_Update)
        dst_ds.SetGeoTransform([c, a, b, f, d, e])
        dst_ds.SetProjection(QgsCoordinateReferenceSystem('EPSG:3857').toWkt(
            QgsCoordinateReferenceSystem.WktVariant.WKT_PREFERRED_GDAL))

        del dst_ds
