# coding=utf-8
"""GUI Utils Test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '20/04/2018'
__copyright__ = 'Copyright 2018, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import unittest
from ..gui import GuiUtils
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class GuiUtilsTest(unittest.TestCase):
    """Test GuiUtils work."""

    def testGetIcon(self):
        """
        Tests get_icon
        """
        self.assertFalse(
            GuiUtils.get_icon('soar_logo.svg').isNull())
        self.assertTrue(GuiUtils.get_icon('not_an_icon.svg').isNull())

    def testGetIconSvg(self):
        """
        Tests get_icon svg path
        """
        self.assertTrue(
            GuiUtils.get_icon_svg('soar_logo.svg'))
        self.assertIn('soar_logo.svg',
                      GuiUtils.get_icon_svg('soar_logo.svg'))
        self.assertFalse(GuiUtils.get_icon_svg('not_an_icon.svg'))

    def testGetUiFilePath(self):
        """
        Tests get_ui_file_path svg path
        """
        self.assertTrue(
            GuiUtils.get_ui_file_path('map_export_dialog.ui'))
        self.assertIn('map_export_dialog.ui',
                      GuiUtils.get_ui_file_path('map_export_dialog.ui'))
        self.assertFalse(GuiUtils.get_ui_file_path('not_a_form.ui'))


if __name__ == "__main__":
    suite = unittest.makeSuite(GuiUtilsTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
