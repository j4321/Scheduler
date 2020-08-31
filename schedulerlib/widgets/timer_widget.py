#!/usr/bin/env python3
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


Timer desktop widget
"""

from tkinter import Text
from tkinter.ttk import Button, Label, Sizegrip, Frame

from PIL.ImageTk import PhotoImage

from schedulerlib.constants import IM_START, IM_PAUSE, IM_STOP, CONFIG
from schedulerlib.ttkwidgets import AutoScrollbar
from .base_widget import BaseWidget


class Timer(BaseWidget):
    def __init__(self, master):
        BaseWidget.__init__(self, 'Timer', master)

    def create_content(self):
        """Create widget's GUI."""
        self.minsize(50, 120)

        self._time = [0, 0, 0]
        self._on = False
        self._after_id = ''

        self.img_play = PhotoImage(master=self, file=IM_START)
        self.img_pause = PhotoImage(master=self, file=IM_PAUSE)
        self.img_stop = PhotoImage(master=self, file=IM_STOP)

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # --- GUI elements
        self.display = Label(self, text='%i:%.2i:%.2i' % tuple(self._time),
                             anchor='center', style='Timer.TLabel')
        interval_frame = Frame(self, style='Timer.TFrame')
        interval_frame.columnconfigure(0, weight=1)
        interval_frame.rowconfigure(0, weight=1)
        sel_bg = self.style.lookup('TEntry', 'selectbackground')
        self.intervals = Text(interval_frame,
                              height=3, width=1, selectbackground=sel_bg,
                              inactiveselectbackground=sel_bg)
        self.intervals.tag_configure('center', justify='center')
        self.intervals.configure(state='disabled')
        scroll = AutoScrollbar(interval_frame, orient='vertical',
                               style='Timer.Vertical.TScrollbar',
                               command=self.intervals.yview)
        self.intervals.configure(yscrollcommand=scroll.set)
        self.intervals.grid(sticky='ewns')
        scroll.grid(row=0, column=1, sticky='ns')
        self.b_interv = Button(self, text=_('Interval'), style='Timer.TButton',
                               command=self.add_interval)
        self.b_interv.state(('disabled',))

        self.b_launch = Button(self, image=self.img_play, padding=2,
                               command=self.launch, style='Timer.TButton')
        self.b_stop = Button(self, image=self.img_stop, padding=2,
                             command=self.stop, style='Timer.TButton')

        # --- placement
        self.display.grid(row=0, columnspan=2, sticky='ew', padx=8, pady=(4, 0))
        Label(self, text=_('Intervals:'),
              style='Timer.TLabel').grid(row=1, columnspan=2, sticky='w', padx=4)
        interval_frame.grid(row=2, columnspan=2, sticky='eswn')
        self.b_interv.grid(row=3, columnspan=2, sticky='ew')
        self.b_launch.grid(row=4, column=0, sticky='ew')
        self.b_stop.grid(row=4, column=1, sticky='ew')

        self._corner = Sizegrip(self, style="Timer.TSizegrip")
        self._corner.place(relx=1, rely=1, anchor='se')

        # --- bindings
        self.intervals.bind("<1>", lambda event: self.intervals.focus_set())
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.display.bind('<ButtonPress-1>', self._start_move)
        self.display.bind('<ButtonRelease-1>', self._stop_move)
        self.display.bind('<B1-Motion>', self._move)
        self.b_stop.bind('<Enter>', self._on_enter)
        self.b_stop.bind('<Leave>', self._on_leave)

    def update_style(self):
        """Update widget's style."""
        BaseWidget.update_style(self)
        self.display.configure(font=CONFIG.get('Timer', 'font_time'))
        self.intervals.configure(bg=CONFIG.get('Timer', 'background'),
                                 fg=CONFIG.get('Timer', 'foreground'),
                                 font=CONFIG.get('Timer', 'font_intervals'))

    def _on_enter(self, event=None):
        self._corner.state(('active',))

    def _on_leave(self, event=None):
        self._corner.state(('!active',))

    def show(self):
        """Show widget."""
        self.deiconify()
        self.update_idletasks()
        self.withdraw()
        if self._position.get() == 'above':
            self.overrideredirect(True)
        else:
            self.overrideredirect(False)
        BaseWidget.show(self)
        self.update_idletasks()
        self.withdraw()
        self.deiconify()

    def _run(self):
        """Count time."""
        if self._on:
            self._time[2] += 1
            if self._time[2] == 60:
                self._time[2] = 0
                self._time[1] += 1
                if self._time[1] == 60:
                    self._time[1] = 0
                    self._time[0] += 1
            self.display.configure(text='%i:%.2i:%.2i' % tuple(self._time))
            self._after_id = self.after(1000, self._run)

    def launch(self):
        """Start/Pause timer."""
        if self._on:
            self._on = False
            self.b_launch.configure(image=self.img_play)
            self.b_interv.state(('disabled',))
        else:
            self._on = True
            self.b_interv.state(('!disabled',))
            self.b_launch.configure(image=self.img_pause)
            self.after(1000, self._run)

    def add_interval(self):
        """Add intreval time to the display."""
        tps = '\n%i:%.2i:%.2i' % tuple(self._time)
        if self.intervals.get('1.0', 'end') == '\n':
            tps = tps[1:]
        self.intervals.configure(state='normal')
        self.intervals.insert('end', tps, 'center')
        self.intervals.configure(state='disabled')

    def stop(self):
        """Stop timer."""
        self._on = False
        self.b_interv.state(('disabled',))
        self.b_launch.configure(image=self.img_play)
        self._time = [0, 0, 0]
        self.intervals.configure(state='normal')
        self.intervals.delete('1.0', 'end')
        self.intervals.configure(state='disabled')
        self.display.configure(text='%i:%.2i:%.2i' % tuple(self._time))


