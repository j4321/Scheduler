#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2016-2019 Juliette Monsel <j_4321@protonmail.com>

Scheduler is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Scheduler is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


System tray icon using Qt.
"""
import sys

try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
    from PyQt5.QtGui import QIcon
except ImportError:
    try:
        from PyQt4.QtGui import QApplication, QSystemTrayIcon, QMenu, QAction, QIcon
    except ImportError:
        from PySide.QtGui import QApplication, QSystemTrayIcon, QMenu, QAction, QIcon


class SubMenu(QMenu):
    """
    Menu or submenu for the system tray icon TrayIcon. 
    
    Qt version.
    """
    def __init__(self, *args, label=None, parent=None, **kwargs):
        """Create a SubMenu instance."""
        if label is None:
            QMenu.__init__(self, parent)
        else:
            QMenu.__init__(self, label, parent)
        self._images = []

    def add_command(self, label="", command=None, image=None):
        """Add an item with given label and associated to given command to the menu."""
        action = QAction(label, self)
        if command is not None:
            action.triggered.connect(lambda *args: command())
        if image is not None:
            self._images.append(QIcon(image))
            action.setIcon(self._images[-1])
        self.addAction(action)

    def add_cascade(self, label="", menu=None, image=None):
        """Add a submenu (SubMenu instance) with given label to the menu."""
        if menu is None:
            menu = SubMenu(label, self)
        action = QAction(label, self)
        action.setMenu(menu)
        if image is not None:
            self._images.append(QIcon(image))
            action.setIcon(self._images[-1])
        self.addAction(action)

    def add_checkbutton(self, label="", command=None):
        """
        Add a checkbutton item with given label and associated to given command to the menu.
        
        The checkbutton state can be obtained/changed using the ``get_item_value``/``set_item_value`` methods.
        """
        action = QAction(label, self)
        action.setCheckable(True)
        if command is not None:
            action.triggered.connect(lambda *args: command())
        self.addAction(action)

    def add_separator(self):
        """Add a separator to the menu."""
        self.addSeparator()

    def delete(self, item1, item2=None):
        """
        Delete all items between item1 and item2 (included).
        
        If item2 is None, delete only the item corresponding to item1. 
        """
        if len(self.actions()) == 0:
            return
        index1 = self.index(item1)
        if item2 is None:
            self.removeAction(self.actions()[index1])
        else:
            index2 = self.index(item2)
            a = self.actions()
            for i in range(index1, index2 + 1):
                self.removeAction(a[i])

    def index(self, item):
        """
        Return the index of item.
        
        item can be an integer corresponding to the entry number in the menu,
        the label of a menu entry or "end". In the fisrt case, the returned index will
        be identical to item.
        """
        if isinstance(item, int):
            if item <= len(self.actions()):
                return item
            else:
                raise ValueError("%r not in menu" % item)
        elif item == "end":
            return len(self.actions())
        else:
            try:
                i = [i.text() for i in self.actions()].index(item)
            except ValueError:
                raise ValueError("%r not in menu" % item)
            return i

    def set_item_image(self, item, image):
        i = self.actions()[self.index(item)]
        try:
            self._images.remove(i.icon())
        except ValueError:
            pass
        self._images.append(QIcon(image))
        i.setIcon(self._images[-1])

    def get_item_label(self, item):
        """Return item's label."""
        return self.actions()[self.index(item)].text()

    def set_item_label(self, item, label):
        """Set the item's label to given label."""
        i = self.actions()[self.index(item)]
        i.setText(label)

    def get_item_menu(self, item):
        """
        Return item's menu.
        
        It is assumed that the item is a cascade.
        """
        i = self.actions()[self.index(item)]
        return i.menu()
        
    def set_item_menu(self, item, menu):
        """
        Set item's menu to given menu (SubMenu instance).
        
        It is assumed that the item is a cascade.
        """
        i = self.actions()[self.index(item)]
        i.setMenu(menu)

    def disable_item(self, item):
        """Put item in disabled (unresponsive) state."""
        self.actions()[self.index(item)].setDisabled(True)

    def enable_item(self, item):
        """Put item in normal (responsive) state."""
        self.actions()[self.index(item)].setDisabled(False)

    def get_item_value(self, item):
        """Return item value (True/False) if item is a checkbutton."""
        return self.actions()[self.index(item)].isChecked()

    def set_item_value(self, item, value):
        """Set item value if item is a checkbutton."""
        i = self.actions()[self.index(item)]
        i.setChecked(value)


class TrayIcon(QApplication):
    """System tray icon, Qt version."""
    def __init__(self, icon, fallback_icon_path, **kwargs):
        """Create a TrayIcon instance."""
        QApplication.__init__(self, sys.argv)
        self._fallback_icon = QIcon(fallback_icon_path)
        self._icon = QIcon.fromTheme(icon, self._fallback_icon)
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self._icon)

        self.menu = SubMenu()
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

    def loop(self, tk_window):
        """Update Qt GUI inside tkinter mainloop."""
        self.processEvents()
        tk_window.loop_id = tk_window.after(10, self.loop, tk_window)

    def change_icon(self, icon, desc=''):
        """Change icon."""
        del self._icon
        self._icon = QIcon(icon)
        self.tray_icon.setIcon(self._icon)

    def bind_left_click(self, command):
        """Bind command to left click on the icon."""
        
        def action(reason):
            """Execute command only on left click (not when the menu is displayed)."""
            if reason == QSystemTrayIcon.Trigger:
                command()

        self.tray_icon.activated.connect(action)

    def bind_middle_click(self, command):
        """Bind command to middle click on the icon."""
        def action(reason):
            """Execute command only on middle click (not when the menu is displayed)."""
            if reason == QSystemTrayIcon.MiddleClick:
                command()

        self.tray_icon.activated.connect(action)

    def bind_double_click(self, command):
        """Bind command to double left click on the icon."""
        def action(reason):
            """Execute command only on double click (not when the menu is displayed)."""
            if reason == QSystemTrayIcon.DoubleClick:
                command()

        self.tray_icon.activated.connect(action)
