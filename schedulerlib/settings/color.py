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


Settings
"""

import tkinter as tk
from tkinter import ttk
from schedulerlib.constants import COLOR, askcolor
from PIL.ImageTk import PhotoImage


class ColorFrame(ttk.Frame):
    def __init__(self, master=None, color='white', label='Color'):
        ttk.Frame.__init__(self, master)
        self._im_color = PhotoImage(master=self, file=COLOR)
        frame = ttk.Frame(self, border=1, relief='groove')
        self.preview = tk.Frame(frame, width=23, height=23, bg=color)
        self.preview.pack()
        ttk.Label(self, text=label).pack(side='left', padx=4, pady=4)
        frame.pack(side='left', padx=4, pady=4)
        ttk.Button(self, image=self._im_color, padding=2,
                   command=self.askcolor).pack(side='left', padx=4, pady=4)

    def askcolor(self):
        try:
            color = askcolor(self.preview.cget('bg'), parent=self, title=_('Color'))
        except tk.TclError:
            color = askcolor(parent=self, title=_('Color'))
        if color is not None:
            self.preview.configure(bg=color)

    def get_color(self):
        return self.preview.cget('bg')
