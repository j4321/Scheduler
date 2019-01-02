#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Scheduler - Task scheduling and calendar
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


System tray icon.
"""


from schedulerlib.constants import GUI

if GUI == 'gtk':
    from schedulerlib.trayicon.gtkicon import TrayIcon, SubMenu
elif GUI == 'qt':
    from schedulerlib.trayicon.qticon import TrayIcon, SubMenu
else:
    from schedulerlib.trayicon.tkicon import TrayIcon, SubMenu
