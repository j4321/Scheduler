#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2018 Juliette Monsel <j_4321@protonmail.com>

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


Task desktop widget
"""

from tkinter import Text
from tkinter.ttk import Label, Separator, Sizegrip
from schedulerlib.constants import CONFIG, TASK_STATE, active_color
from schedulerlib.ttkwidgets import AutoScrollbar
from .base_widget import BaseWidget


class TaskWidget(BaseWidget):
    def __init__(self, master):
        BaseWidget.__init__(self, 'Tasks', master)

    def create_content(self, **kw):
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.minsize(50, 50)
        self.hide_completed = CONFIG.getboolean('Tasks', 'hide_completed')

        # --- elements
        label = Label(self, text=_('Tasks').upper(), style='title.Tasks.TLabel',
                      anchor='center')
        label.grid(row=0, columnspan=2, pady=4, sticky='ew')
        Separator(self, style='Tasks.TSeparator').grid(row=1, columnspan=2, sticky='we')
        self.display = Text(self, width=20, height=10, relief='flat',
                            cursor='arrow', wrap='word',
                            highlightthickness=0, state='disabled',
                            spacing1=5,
                            tabs=('35', 'right', '45', 'left'))
        self.display.grid(sticky='nsew', row=2, column=0, padx=2, pady=2)
        scroll = AutoScrollbar(self, orient='vertical',
                               style='Tasks.Vertical.TScrollbar',
                               command=self.display.yview)
        scroll.grid(row=2, column=1, sticky='ns', pady=(2, 16))
        self.display.configure(yscrollcommand=scroll.set)
        self.display_tasks()

        corner = Sizegrip(self, style="Tasks.TSizegrip")
        corner.place(relx=1, rely=1, anchor='se')

        # --- bindings
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        label.bind('<ButtonPress-1>', self._start_move)
        label.bind('<ButtonRelease-1>', self._stop_move)
        label.bind('<B1-Motion>', self._move)

    def update_style(self):
        self.attributes('-alpha', CONFIG.get(self.name, 'alpha', fallback=0.85))
        bg = CONFIG.get('Tasks', 'background')
        fg = CONFIG.get('Tasks', 'foreground')
        active_bg = active_color(*self.winfo_rgb(bg))
        self.style.configure('Tasks.TFrame', background=bg)
        self.style.configure('Tasks.TSizegrip', background=bg)
        self.style.configure('Tasks.TSeparator', background=bg)
        self.style.configure('Tasks.TLabel', background=bg, foreground=fg,
                             font=CONFIG.get('Tasks', 'font'))
        self.style.configure('title.Tasks.TLabel',
                             font=CONFIG.get('Tasks', 'font_title'))
        self.configure(bg=bg)
        self.menu.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                            activebackground=active_bg)
        self.menu_pos.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                                activebackground=active_bg)
        self.display.configure(selectbackground=bg,
                               inactiveselectbackground=bg,
                               selectforeground=fg,
                               background=bg, foreground=fg,
                               font=CONFIG.get('Tasks', 'font'))

    def display_tasks(self, force=False):
        tasks = self.master.get_tasks()
        tasks.sort(key=lambda ev: ev['End'])
        self.display.configure(state='normal')
        self.display.delete('1.0', 'end')
        for ev in tasks:
            if not self.hide_completed or ev['Task'] != 'Completed':
                if ev["WholeDay"]:
                    end = ev['End'].strftime('%x')
                else:
                    end = ev['End'].strftime('%x %H:%M')
                picto = TASK_STATE.get(ev['Task'], ev['Task'])
                txt = "\t%s\t%s [%s]\n" % (picto, ev['Summary'], end)
                self.display.insert('end', txt)
        self.display.configure(state='disabled')
