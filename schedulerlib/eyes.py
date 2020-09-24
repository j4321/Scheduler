#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2019 Juliette Monsel <j_4321@protonmail.com>

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


Eyes' rest script
"""
from subprocess import Popen

from .constants import IM_EYE, IMAGES, CONFIG
from .trayicon import SubMenu


class Eyes(SubMenu):
    """Eyes' rest submenu."""
    def __init__(self, parent, tkwindow):
        SubMenu.__init__(self, parent=parent)
        self.time = [0, 0]
        self.is_on = False
        self.tkwindow = tkwindow
        self._after_id = None

        self.add_command(label=_('Start'), command=self.start_stop, image=IMAGES['start_m'])
        self.add_command(label=_('Status'), command=self.status)

    def quit(self):
        try:
            self.tkwindow.after_cancel(self._after_id)
        except ValueError:
            pass

    def start_stop(self):
        if self.is_on:
            self.is_on = False
            self.time = [0, 0]
            self.set_item_label(0, _('Start'))
            self.set_item_image(0, IMAGES['start_m'])
        else:
            self.is_on = True
            Popen(["notify-send", "-i", IM_EYE, "Scheduler",
                   _("The eyes' rest script has been launched!")])
            self.set_item_label(0, _('Stop'))
            self.set_item_image(0, IMAGES['stop_m'])
            self._after_id = self.tkwindow.after(1000, self.timer)

    def timer(self):
        if self.is_on:
            self.time[1] += 1
            if self.time[1] == 60:
                self.time[1] = 0
                self.time[0] += 1
                if self.time[0] >= CONFIG.getint("Eyes", "interval"):
                    Popen(["notify-send", "-i", IM_EYE, _("Eyes' rest"),
                           _("Look away from your screen for 20 s")])
                    if (not CONFIG.getboolean("Eyes", "mute") and
                            not CONFIG.getboolean('General', 'silent_mode')):
                        Popen([CONFIG.get("General", "soundplayer"),
                               CONFIG.get("Eyes", "sound")])

                    self.time[0] = 0

            self._after_id = self.tkwindow.after(1000, self.timer)

    def status(self):
        if self.is_on:
            Popen(["notify-send", "-i", IM_EYE, "Scheduler",
                   _("Time since last eyes' rest: {min} min {sec} s").format(min=self.time[0], sec=self.time[1])])
        else:
            Popen(["notify-send", "-i", IM_EYE, "Scheduler",
                   _("The eyes' rest script is not active.")])
