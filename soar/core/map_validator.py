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

from qgis.PyQt.QtCore import QObject

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProject
)


class ValidationError(Exception):
    """
    Raised when a validation check fails
    """


class MapValidator(QObject):
    """
    Responsible for validating maps prior to publishing to soar
    """

    def __init__(self, project: QgsProject):
        super().__init__()
        self.project = project
        self._error_list = []

    def validate(self) -> bool:
        """
        Validates the project
        """

        checks = [self.check_crs]
        self._error_list = []
        for check in checks:
            try:
                check()
            except ValidationError as e:
                self._error_list.append(str(e))

        return not self._error_list

    def error_message(self) -> str:
        """
        Returns a HTML formatted descriptive error message when validation fails
        """
        if not self._error_list:
            return ''

        error_list = '\n'.join(["<li>{}</li>".format(e) for e in self._error_list])

        description = self.tr('Map cannot be exported to Soar:')
        return '<p style="color: red; font-weight: bold">{}</p><ul>{}</ul>'.format(description, error_list)

    def check_crs(self):
        """
        Checks whether the project's CRS is compatible with soar.earth
        """
        if self.project.crs() != QgsCoordinateReferenceSystem('EPSG:3857'):
            raise ValidationError(self.tr(
                'Maps published on Soar must be created using the Web Mercator projection '
                '(EPSG:3857). Please change your project\'s CRS to EPSG:3857 and re-try.'))
