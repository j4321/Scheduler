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


Settings
"""
from tkinter import ttk

from schedulerlib.ttkwidgets import ScaleEntry


class OpacityFrame(ttk.Frame):
    def __init__(self, master=None, value=0.85, style='title.TLabel', **kw):
        ttk.Frame.__init__(self, master, **kw)

        self.columnconfigure(1, weight=1)
        self.opacity_scale = ScaleEntry(self, orient="horizontal", scalewidth=300,
                                        from_=0, to=100, entryscalepad=10,
                                        value=int(value * 100))
        ttk.Label(self, style=style,
                  text=_("Opacity")).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=4)
        self.opacity_scale.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(self, text='%').grid(row=0, column=2, sticky="w", padx=(0, 4), pady=4)

    def get_opacity(self):
        return int(float(self.opacity_scale.value)) / 100
