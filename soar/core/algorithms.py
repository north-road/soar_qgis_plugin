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

from qgis.PyQt.QtCore import (
    QEventLoop
)

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterEnum,
    QgsCoordinateTransform,
    QgsProcessingException,
    QgsRasterFileWriter,
    QgsProcessingUtils,
    QgsRasterPipe,
    QgsProcessingParameterString,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterBoolean,
    QgsRasterProjector,
    QgsRasterBlockFeedback
)

from .client import API_CLIENT
from .map_exporter import MapExportSettings
from ..gui import LOGIN_MANAGER


class PublishRasterToSoar(QgsProcessingAlgorithm):
    """
    Publishes raster datasets to soar.earth
    """

    INPUT = 'INPUT'
    MODE = 'MODE'
    TITLE = 'TITLE'
    DESCRIPTION = 'DESCRIPTION'
    TAGS = 'TAGS'
    CATEGORY = 'CATEGORY'
    OWN_WORK = 'OWN_WORK'
    ACCEPT_TERMS = 'ACCEPT_TERMS'

    CATEGORY_STRINGS = ['Agriculture',
                        'Climate',
                        'Earth Art',
                        'Economic',
                        'Geology',
                        'History',
                        'Marine',
                        'Political',
                        'Terrain',
                        'Transport',
                        'Urban']
    CATEGORY_RAW = [
        'agriculture',
        'climate',
        'earth-art',
        'economic',
        'geology',
        'history',
        'marine',
        'political',
        'terrain',
        'transport',
        'urban'
    ]

    # pylint: disable=missing-docstring,unused-argument

    def __init__(self):
        super().__init__()

        self.data_provider = None
        self.original_pipe = None

    def createInstance(self):
        return PublishRasterToSoar()

    def name(self):
        return 'tifftosoar'

    def displayName(self):
        return 'Publish dataset to soar.earth'

    def shortDescription(self):
        return 'Publishes a GeoTIFF dataset to soar.earth'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def shortHelpString(self):
        return "Publishes a GeoTIFF dataset to soar.earth"

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT, 'Source layer'))

        self.addParameter(
            QgsProcessingParameterString(
                self.TITLE,
                'Map title',
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.DESCRIPTION,
                'Description',
                multiLine=True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.TAGS,
                'Tags (; separated)',
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.CATEGORY,
                'Category',
                self.CATEGORY_STRINGS
            )
        )

        self.addParameter(QgsProcessingParameterEnum(
            self.MODE,
            'Export mode',
            ['Raw data', 'Rendered layer'],
            defaultValue=0
        ))

        self.addParameter(QgsProcessingParameterBoolean(
            self.OWN_WORK,
            'This is my own work and/or I have the right to publish this content.',
            False
        ))

        self.addParameter(QgsProcessingParameterBoolean(
            self.ACCEPT_TERMS,
            'I agree to the soar.earth Terms of Service.',
            False
        ))

    @staticmethod
    def clone_pipe(pipe: QgsRasterPipe) -> QgsRasterPipe:
        res = QgsRasterPipe()

        for i in range(pipe.size()):
            res.insert(i, pipe.at(i).clone())

        return res

    def prepareAlgorithm(self, parameters, context, feedback):
        if not LOGIN_MANAGER.is_logged_in():
            loop = QEventLoop()
            LOGIN_MANAGER.logged_in.connect(loop.quit)
            LOGIN_MANAGER.login_failed.connect(loop.quit)

            LOGIN_MANAGER.start_login()
            loop.exec()

            if not LOGIN_MANAGER.is_logged_in():
                return False

        input_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        self.data_provider = input_layer.dataProvider().clone()
        self.original_pipe = self.clone_pipe(input_layer.pipe())

        return True

    def processAlgorithm(self,
                         # pylint: disable=too-many-locals,too-many-statements,too-many-return-statements
                         parameters,
                         context,
                         feedback):

        if not self.parameterAsBool(parameters, self.OWN_WORK, context):
            raise QgsProcessingException('You must confirm that this is your own work or you have rights to publish this content')

        if not self.parameterAsBool(parameters, self.ACCEPT_TERMS, context):
            raise QgsProcessingException('You must accept the soar.earth Terms of Service')

        mode = self.parameterAsEnum(parameters, self.MODE, context)
        title = self.parameterAsString(parameters, self.TITLE, context)
        if not title:
            raise QgsProcessingException('A title is required')
        description = self.parameterAsString(parameters, self.DESCRIPTION, context)
        if not description:
            raise QgsProcessingException('A description is required')
        tags = self.parameterAsString(parameters, self.TAGS, context).split(';')
        if not tags:
            raise QgsProcessingException('Some tags are required')

        category = self.CATEGORY_RAW[self.parameterAsEnum(parameters, self.CATEGORY, context)]

        # prepare layer -- export to EPSG:3857
        temp_file = QgsProcessingUtils.generateTempFilename('qgis_soar_export.tif')
        writer = QgsRasterFileWriter(temp_file)
        writer.setOutputFormat('GTIFF')

        extent = self.data_provider.extent()
        transform = QgsCoordinateTransform(self.data_provider.crs(),
                                           QgsCoordinateReferenceSystem('EPSG:3857'),
                                           context.transformContext()
                                           )

        if mode == 0:
            pipe = QgsRasterPipe()
            pipe.set(self.data_provider.clone())

            # TODO
            # nuller = QgsRasterNuller()
            # for band in range(1, self.data_provider.bandCount() + 1):
            #    if self.data_provider.sourceHasNoDataValue(band):
            #        nuller.setNoData(band, self.data_provider.sourceNoDataValue(band))
            # pipe.insert(1, nuller)

            if self.data_provider.crs() != QgsCoordinateReferenceSystem('EPSG:3857'):
                projector = QgsRasterProjector()
                projector.setCrs(self.data_provider.crs(),
                                 QgsCoordinateReferenceSystem('EPSG:3857'),
                                 context.transformContext()
                                 )
                pipe.insert(2, projector)

                extent = transform.transformBoundingBox(extent)
        else:
            # rendered image mode
            pipe = self.clone_pipe(self.original_pipe)

            projector = pipe.projector()
            if self.data_provider.crs() != QgsCoordinateReferenceSystem('EPSG:3857'):
                projector.setCrs(self.data_provider.crs(),
                                 QgsCoordinateReferenceSystem('EPSG:3857'),
                                 context.transformContext()
                                 )

                extent = transform.transformBoundingBox(extent)

        writer_feedback = QgsRasterBlockFeedback()
        res = writer.writeRaster(pipe,
                                 self.data_provider.xSize(),
                                 self.data_provider.ySize(),
                                 extent,
                                 QgsCoordinateReferenceSystem('EPSG:3857'),
                                 context.transformContext(),
                                 writer_feedback)

        if res != QgsRasterFileWriter.NoError:
            raise QgsProcessingException(
                'An error occurred: {}'.format('\n'.join(writer_feedback.errors())))

        from .client import API_CLIENT

        settings = MapExportSettings()
        settings.title = title
        settings.description = description
        settings.tags = tags
        settings.category = category
        settings.output_file_name = temp_file
        upload_start_reply = API_CLIENT.request_upload_start(settings)

        loop = QEventLoop()
        upload_start_reply.finished.connect(loop.quit)
        loop.exec()

        res, error = API_CLIENT.parse_request_upload_reply(upload_start_reply)

        if res is None:
            # error occurred
            if error:
                raise QgsProcessingException(error)
            else:
                raise QgsProcessingException('Upload failed for unknown reason')

        try:
            API_CLIENT.upload_file(temp_file, res)
            feedback.pushInfo('Dataset successfully uploaded')
        except Exception as e:
            raise QgsProcessingException(str(e))

        return {}

    # pylint: enable=missing-docstring,unused-argument
