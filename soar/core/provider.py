# -*- coding: utf-8 -*-
"""Soar.earth processing library

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


from qgis.core import QgsProcessingProvider

from .algorithms import (
    PublishRasterToSoar
)
from ..gui import GuiUtils


class SoarEarthProvider(QgsProcessingProvider):
    """
    Soar Processing provider
    """

    def __init__(self):  # pylint: disable=useless-super-delegation
        super().__init__()

    def loadAlgorithms(self):  # pylint: disable=missing-docstring
        for alg in [PublishRasterToSoar]:
            self.addAlgorithm(alg())

    def id(self):  # pylint: disable=missing-docstring
        return 'soar'

    def name(self):  # pylint: disable=missing-docstring
        return 'Soar'

    def longName(self):  # pylint: disable=missing-docstring
        return 'Soar map publishing tools'

    def icon(self):  # pylint: disable=missing-docstring
        return GuiUtils.get_icon('soar_provider.svg')

    def versionInfo(self):
        # pylint: disable=missing-docstring
        return '0.0.8'
