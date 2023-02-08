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

from typing import List

from qgis.PyQt.QtCore import (
    QSize
)
from qgis.core import (
    Qgis,
    QgsProject,
    QgsRectangle,
    QgsMapSettings,
    QgsCoordinateReferenceSystem,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsMapRendererTask,
    QgsTask
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
        self.category: str = ''
        self.size: QSize = QSize()
        self.scale: float = 0
        self.extent: QgsRectangle = QgsRectangle()

    def map_settings(self, map_canvas: QgsMapCanvas) -> QgsMapSettings:
        """
        Converts the settings to a QgsMapSettings object
        """
        ms = QgsMapSettings()
        ms.setFlag(QgsMapSettings.Antialiasing, True)
        try:
            ms.setFlag(QgsMapSettings.HighQualityImageTransforms, True)
        except AttributeError:
            pass
        ms.setFlag(QgsMapSettings.ForceVectorOutput, True)
        ms.setFlag(QgsMapSettings.DrawEditingInfo, False)
        ms.setFlag(QgsMapSettings.DrawSelection, False)
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
        expression_context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
        expression_context.appendScope(QgsExpressionContextUtils.mapSettingsScope(ms))

        ms.setExpressionContext(expression_context)
        try:
            ms.setRendererUsage(Qgis.RendererUsage.Export)
        except AttributeError:
            pass

        return ms


class MapPublisher(QgsTask):

    def __init__(self, settings: MapExportSettings, canvas: QgsMapCanvas):
        super().__init__('Publishing map to Soar.earth', QgsTask.Flag.CanCancel)

        self.settings = settings
        self.map_settings = self.settings.map_settings(canvas)

        self.addSubTask(QgsMapRendererTask(self.map_settings,'/home/nyall/test.png'), subTaskDependency=QgsTask.ParentDependsOnSubTask)

    def run(self) -> bool:
        print('ok done, ready for upload')

        return True
