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

from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QRect,
    QSize,
    pyqtSignal
)
from qgis.PyQt.QtWidgets import (
    QLayout,
    QSizePolicy,
    QStyle,
    QWidget,
    QWidgetItem
)

from .listing_items import (
    EmptyDatasetItemWidget,
    ListingItemWidget
)
from ..core.client import Listing


class ResponsiveTableLayout(QLayout):
    """
    A responsive table layout which dynamically flows to multiple columns
    """

    def __init__(self, parent, hspacing, vspacing):
        super().__init__(parent)

        self.hspacing = hspacing
        self.vspacing = vspacing

        self._column_count = 1

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    # QLayout interface
    # pylint: disable=missing-function-docstring
    def addItem(self, item):
        self.itemList.append(item)

    def horizontalSpacing(self):
        if self.hspacing >= 0:
            return self.hspacing
        return self.smart_spacing(QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self.vspacing >= 0:
            return self.vspacing
        return self.smart_spacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientations()  # Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                      margins.top() + margins.bottom())
        return size

    # pylint: enable=missing-function-docstring

    def insert_widget(self, idx: int, widget: QWidget):
        """
        Inserts a widget into the layout at a given index
        """
        self.addChildWidget(widget)
        item = QWidgetItem(widget)
        self.itemList.insert(idx, item)
        self.invalidate()

    def column_count(self) -> int:
        """
        Returns the current column count
        """
        return self._column_count

    def _do_layout(self, rect, test_only):  # pylint: disable=too-many-locals
        """
        Calculates the layout
        """
        margins = self.contentsMargins()
        left = margins.left()
        top = margins.top()
        right = margins.right()
        bottom = margins.bottom()

        effective_rect = rect.adjusted(left, top, -right, -bottom)

        col_count = int(effective_rect.width() / 400)

        col_count = max(1, col_count)

        space_x = self.horizontalSpacing()
        space_y = self.verticalSpacing()

        width_without_spacing = effective_rect.width() - (col_count - 1) * space_x
        col_width = int(width_without_spacing / col_count)

        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        y_offsets = [y]

        assigned_lines = []
        current_line_items = []

        visible_items = [i for i in self.itemList if not i.widget().isHidden()]

        if not visible_items:
            return 0

        for item in visible_items:
            next_x = x + col_width + space_x

            current_line_items.append(item)
            line_height = max(line_height, item.sizeHint().height())
            if len(current_line_items) == col_count:
                assigned_lines.append(current_line_items[:])
                current_line_items = []

                x = effective_rect.x()
                y = y + line_height + space_y
                y_offsets.append(y)

                next_x = x + item.minimumSize().width() + space_x
                line_height = 0

            x = next_x

        if current_line_items:
            assigned_lines.append(current_line_items[:])

        if not test_only:
            self._column_count = col_count
            for idx, line in enumerate(assigned_lines):
                y_offset = y_offsets[idx]

                x = effective_rect.left()
                for item in line:
                    item.setGeometry(
                        QRect(x, y_offset, col_width, item.sizeHint().height())
                    )

                    x += col_width + space_x

        return y + line_height - rect.y() + bottom

    def smart_spacing(self, pm) -> int:
        """
        Calculates spacing for the layout
        """
        parent = self.parent()
        if not parent:
            return -1

        if parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)

        return parent.spacing()


class ResponsiveTableWidget(QWidget):
    """
    A responsive table widget for showing listing results
    """
    VERTICAL_SPACING = 10
    HORIZONTAL_SPACING = 10

    listing_clicked = pyqtSignal(Listing)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setLayout(ResponsiveTableLayout(parent=None, vspacing=self.VERTICAL_SPACING,
                                             hspacing=self.HORIZONTAL_SPACING))

        self.layout().setContentsMargins(0, 0, 16, 16)

        self._widgets = []

    def clear(self):
        """
        Clears all listings from the table
        """
        for w in self._widgets:
            w.deleteLater()
            self.layout().takeAt(0)
        self._widgets = []

    def column_count(self):
        """
        Returns the table column count
        """
        return self.layout().column_count()

    def push_empty_widget(self):
        """
        Pushes an empty entry into the table
        """
        empty_widget = EmptyDatasetItemWidget()
        self.push_widget(empty_widget)

    def find_next_empty_widget(self) -> Optional[QWidget]:
        """
        Finds the next available empty space
        """

        for w in self._widgets:
            if isinstance(w, EmptyDatasetItemWidget):
                return w

        return None

    def replace_widget(self, old_widget, new_widget):
        """
        Replaces a widget in the table
        """
        idx = self._widgets.index(old_widget)
        self._widgets[idx].setParent(None)
        self._widgets[idx].deleteLater()

        self._widgets[idx] = new_widget
        self._widgets[idx].setParent(self)

        self.layout().insert_widget(idx, new_widget)

        self.layout().takeAt(idx + 1)

    def push_listing(self, listing: Listing):
        """
        Pushes a listing to the table
        """
        listing_widget = ListingItemWidget(listing, self)
        listing_widget.clicked.connect(self.listing_clicked)

        next_empty_widget = self.find_next_empty_widget()
        if next_empty_widget is not None:
            self.replace_widget(next_empty_widget, listing_widget)
        else:
            self.push_widget(listing_widget)

    def push_widget(self, widget):
        """
        Pushes a widget to the table
        """
        self._widgets.append(widget)
        self.layout().addWidget(widget)

    def remove_empty_widgets(self):
        """
        Removes all empty widgets from the table
        """
        self.setUpdatesEnabled(False)
        for idx in range(len(self._widgets) - 1, -1, -1):
            if isinstance(self._widgets[idx], EmptyDatasetItemWidget):
                self._widgets[idx].setParent(None)
                self._widgets[idx].deleteLater()
                self.layout().takeAt(idx)
                del self._widgets[idx]
        self.setUpdatesEnabled(True)

    def remove_widget(self, widget):
        """
        Removes a widget from the table
        """
        idx = self._widgets.index(widget)
        self._widgets[idx].setParent(None)
        self._widgets[idx].deleteLater()
        self.layout().takeAt(idx)
        del self._widgets[idx]
