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


Settings: Sound file
"""
import os
import tkinter as tk
from tkinter import ttk

from schedulerlib.constants import askopenfilename


class SoundFrame(ttk.Frame):
    def __init__(self, master=None, soundfile='', mute=False, label='', **kw):
        ttk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)

        self.mute = tk.BooleanVar(self, mute)
        frame = ttk.Frame(self)
        self.label = ttk.Label(frame, text=label, **kw)
        self.label.pack(side='left', pady=4, padx=(0, 4))
        self.mute_btn = ttk.Checkbutton(frame, variable=self.mute,
                                        command=self._toggle, style='Mute')
        self.mute_btn.pack(side='left', pady=4, padx=6)
        self.path = ttk.Entry(self)
        self._soundfile = soundfile
        self.path.insert(0, soundfile)
        self.b_choose = ttk.Button(self, text="...", width=2, padding=0,
                                   command=self.choose)
        # --- placement
        frame.grid(row=0, columnspan=2, sticky='w')
        self.path.grid(column=0, row=1, sticky='ew', padx=(4, 0))
        self.b_choose.grid(column=1, row=1, padx=(2, 0))
        self._toggle()

    def state(self, statespec=None):
        self.path.state(statespec)
        self.b_choose.state(statespec)
        self.mute_btn.state(statespec)
        self.label.state(statespec)
        return ttk.Frame.state(self, statespec)

    def _toggle(self):
        if self.mute.get():
            self.path.state(['disabled'])
            self.b_choose.state(['disabled'])
        else:
            self.path.state(['!disabled'])
            self.b_choose.state(['!disabled'])

    def choose(self):
        filetypes = [('MP3', '*.mp3'), (_("All files"), "*")]
        init = self.path.get()
        if not os.path.exists(init):
            init = self._soundfile
        initialdir, initialfile = os.path.split(init)
        fich = askopenfilename(filetypes=filetypes, initialfile=initialfile,
                               initialdir=initialdir, parent=self)
        if fich:
            self.path.delete(0, "end")
            self.path.insert(0, fich)

    def get(self):
        return self.path.get(), self.mute.get()
