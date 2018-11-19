#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Scheduler - System tray unread mail checker
Copyright 2016-2018 Juliette Monsel <j_4321@protonmail.com>

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


System tray icon using Gtk 3.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APPIND_SUPPORT = 1
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except ValueError:
    APPIND_SUPPORT = 0


class ImageMenuItem(Gtk.MenuItem):
    def __init__(self, label='', image=None):
        Gtk.MenuItem.__init__(self)
        self.box = Gtk.Box(spacing=6)
        self.label = Gtk.Label(label=label)
        self.image = Gtk.Image()
        if image is not None:
            print(image)
            self.image.set_from_file(image)
        self.add(self.box)
        self.box.pack_start(self.image, False, False, 0)
        self.box.pack_start(self.label, False, False, 0)

        self.set_label = self.label.set_label
        self.get_label = self.label.get_label


class SubMenu(Gtk.Menu):
    """
    Menu or submenu for the system tray icon TrayIcon.

    Gtk version.
    """
    def __init__(self, *args, **kwargs):
        """Create a SubMenu instance."""
        Gtk.Menu.__init__(self)

    def add_command(self, label="", command=None, image=None):
        """Add an item with given label and associated to given command to the menu."""
        item = ImageMenuItem(label=label, image=image)
        self.append(item)
        if command is not None:
            item.connect("activate", lambda *args: command())
        item.show_all()

    def add_cascade(self, label="", menu=None, image=None):
        """Add a submenu (SubMenu instance) with given label to the menu."""
        item = ImageMenuItem(label=label, image=image)
        self.append(item)
        if menu is not None:
            item.set_submenu(menu)
        item.show_all()

    def add_checkbutton(self, label="", command=None):
        """
        Add a checkbutton item with given label and associated to given command to the menu.

        The checkbutton state can be obtained/changed using the ``get_item_value``/``set_item_value`` methods.
        """
        item = Gtk.CheckMenuItem(label=label)
        self.append(item)
        if command is not None:
            item.connect("activate", lambda *args: command())
        item.show()

    def add_separator(self):
        """Add a separator to the menu."""
        sep = Gtk.SeparatorMenuItem()
        self.append(sep)
        sep.show()

    def delete(self, item1, item2=None):
        """
        Delete all items between item1 and item2 (included).

        If item2 is None, delete only the item corresponding to item1.
        """
        if len(self.get_children()) == 0:
            return
        index1 = self.index(item1)
        if item2 is None:
            self.remove(self.get_children()[index1])
        else:
            index2 = self.index(item2)
            c = self.get_children()
            for i in range(index1, index2 + 1):
                self.remove(c[i])

    def index(self, item):
        """
        Return the index of item.

        item can be an integer corresponding to the entry number in the menu,
        the label of a menu entry or "end". In the fisrt case, the returned index will
        be identical to item.
        """
        if isinstance(item, int):
            if item <= len(self.get_children()):
                return item
            else:
                raise ValueError("%r not in menu" % item)
        elif item == "end":
            return len(self.get_children())
        else:
            try:
                i = [i.get_label() for i in self.get_children()].index(item)
            except ValueError:
                raise ValueError("%r not in menu" % item)
            return i

    def set_item_image(self, item, image):
        item = self.get_children()[self.index(item)]
        if image is not None:
            item.image.set_from_file(image)

    def get_item_label(self, item):
        """Return item's label."""
        return self.get_children()[self.index(item)].get_label()

    def set_item_label(self, item, label):
        """Set the item's label to given label."""
        self.get_children()[self.index(item)].set_label(label)

    def get_item_menu(self, item):
        """
        Return item's menu.

        It is assumed that the item is a cascade.
        """
        return self.get_children()[self.index(item)].get_submenu()

    def set_item_menu(self, item, menu):
        """
        Set item's menu to given menu (SubMenu instance).

        It is assumed that the item is a cascade.
        """
        self.get_children()[self.index(item)].set_submenu(menu)

    def disable_item(self, item):
        """Put item in disabled (unresponsive) state."""
        self.get_children()[self.index(item)].set_sensitive(False)

    def enable_item(self, item):
        """Put item in normal (responsive) state."""
        self.get_children()[self.index(item)].set_sensitive(True)

    def get_item_value(self, item):
        """Return item value (True/False) if item is a checkbutton."""
        return self.get_children()[self.index(item)].get_active()

    def set_item_value(self, item, value):
        """Set item value if item is a checkbutton."""
        i = self.get_children()[self.index(item)]
        i.set_active(value)


class TrayIcon:
    """System tray icon, Gtk version."""
    def __init__(self, icon, fallback_icon_path, appid="TrayIcon", **kwargs):
        """Create a TrayIcon instance."""

        self.menu = SubMenu()

        icon_exists = Gtk.IconTheme.get_default().has_icon(icon)

        if APPIND_SUPPORT == 1:
            if icon_exists:
                self.tray_icon = AppIndicator3.Indicator.new(appid, icon,
                                                             AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            else:
                self.tray_icon = AppIndicator3.Indicator.new(appid,
                                                             fallback_icon_path,
                                                             AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.tray_icon.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.tray_icon.set_menu(self.menu)
            self.change_icon = self._change_icon_appind
        else:
            if icon_exists:
                self.tray_icon = Gtk.StatusIcon.new_from_icon_name(icon)
            else:
                self.tray_icon = Gtk.StatusIcon.new_from_file(fallback_icon_path)
            self.tray_icon.connect('popup-menu', self._on_popup_menu)
            self.change_icon = self._change_icon_fallback

    def _on_popup_menu(self, icon, button, time):
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, time)

    def _change_icon_appind(self, icon, desc):
        self.tray_icon.set_icon_full(icon, desc)

    def _change_icon_fallback(self, icon, desc):
        self.tray_icon.set_from_file(icon)

    def loop(self, tk_window):
        """Update Gtk GUI inside tkinter mainloop."""
        while Gtk.events_pending():
            Gtk.main_iteration()
        tk_window.loop_id = tk_window.after(10, self.loop, tk_window)

    def bind_left_click(self, command):
        if not APPIND_SUPPORT:
            self.tray_icon.connect('activate', lambda *args: command())

