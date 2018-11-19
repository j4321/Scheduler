#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2018 Juliette Monsel <j_4321@protonmail.com>
code based on http://effbot.org/zone/tkinter-autoscrollbar.htm

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
from .constants import IM_EYE, IM_START, IM_STOP
from .trayicon import SubMenu


class Eyes(SubMenu):
    def __init__(self, parent, tkwindow):
        SubMenu.__init__(self, parent=parent)
        self.chrono = [0, 0]
        self.marche = False
        self.tkwindow = tkwindow
        self._after_id = None

        self.add_command(label=_('Start'), command=self.lance, image=IM_START)
        self.add_command(label=_('Status'), command=self.affiche)

    def quit(self):
        try:
            self.tkwindow.after_cancel(self._after_id)
        except ValueError:
            pass

    def lance(self):
        if self.marche:
            self.marche = False
            self.chrono = [0, 0]
            self.set_item_image(0, _('Start'))
            self.set_item_image(0, IM_START)
        else:
            self.marche = True
            Popen(["notify-send", "-i", IM_EYE, _("Scheduler"),
                   _("The eyes' rest script has been launched!")])
            self.set_item_label(0, _('Stop'))
            self.set_item_image(0, IM_STOP)
            self._after_id = self.tkwindow.after(1000, self.compte)

    def compte(self):
        if self.marche:
            self.chrono[1] += 1
            if self.chrono[1] == 60:
                self.chrono[1] = 0
                self.chrono[0] += 1
                if self.chrono[0] == 20:
                    Popen(["notify-send", "-i", IM_EYE, _("Eyes' rest"),
                           _("Look away from your screen for 20 s")])
                    self.chrono[0] = 0

            self._after_id = self.tkwindow.after(1000, self.compte)

    def affiche(self):
        if self.marche:
            Popen(["notify-send", "-i", IM_EYE, _("Scheduler"),
                   _("Time since last eye rest: {min} min {sec} s").format(min=self.chrono[0], sec=self.chrono[1])])
        else:
            Popen(["notify-send", "-i", IM_EYE, _("Scheduler"),
                   _("The eyes' rest' script is not active.")])
