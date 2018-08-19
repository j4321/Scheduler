#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017 Juliette Monsel <j_4321@protonmail.com>
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


Task desktop widget
"""

from tkinter import Toplevel, Text, BooleanVar, Menu, StringVar
from tkinter.ttk import Style, Label, Separator, Sizegrip
from schedulerlib.constants import CONFIG, TASK_STATE
from schedulerlib.ttkwidgets import AutoScrollbar
from ewmh import EWMH


class TaskWidget(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.attributes('-type', 'splash')
        self.attributes('-alpha', CONFIG.get('General', 'alpha'))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.minsize(50, 50)
        self.hide_completed = CONFIG.getboolean('Tasks', 'hide_completed')

        self._position = StringVar(self, CONFIG.get('Tasks', 'position'))
        self._position.trace_add('write', lambda *x: CONFIG.set('Tasks', 'position', self._position.get()))

        self.ewmh = EWMH()
        self.title('scheduler.tasks')
        self.withdraw()

        # control main menu checkbutton
        self.variable = BooleanVar(self, False)

        # --- style
        bg = CONFIG.get('Tasks', 'background')
        fg = CONFIG.get('Tasks', 'foreground')
        self.configure(bg=bg)

        style = Style(self)
        style.configure('Tasks.TFrame', background=bg)
        style.configure('Tasks.TSizegrip', background=bg)
        style.configure('Tasks.TSeparator', background=bg)
        style.configure('Tasks.TLabel', background=bg, foreground=fg)

        # --- menu
        self.menu = Menu(self, tearoff=False)
        menu_pos = Menu(self.menu, tearoff=False)
        menu_pos.add_radiobutton(label='Normal', value='normal',
                                 variable=self._position, command=self._on_map)
        menu_pos.add_radiobutton(label='Above', value='above',
                                 variable=self._position, command=self._on_map)
        menu_pos.add_radiobutton(label='Below', value='below',
                                 variable=self._position, command=self._on_map)
        self.menu.add_cascade(label='Position', menu=menu_pos)
        self.menu.add_command(label='Hide', command=self.withdraw)

        # --- elements
        label = Label(self, text='TASKS', style='Tasks.TLabel',
                      anchor='center', font=CONFIG.get('Tasks', 'font_title'))
        label.grid(row=0, columnspan=2, pady=4, sticky='ew')
        Separator(self, style='Tasks.TSeparator').grid(row=1, columnspan=2, sticky='we')
        self.display = Text(self, width=20, height=10, relief='flat',
                            cursor='arrow', wrap='word',
                            highlightthickness=0, state='disabled',
                            selectbackground=bg,
                            inactiveselectbackground=bg,
                            selectforeground=fg,
                            spacing1=5,
                            tabs=('35', 'right', '45', 'left'),
                            background=bg, foreground=fg,
                            font=CONFIG.get('Tasks', 'font'))
        self.display.grid(sticky='nsew', row=2, column=0, padx=2, pady=2)
        scroll = AutoScrollbar(self, orient='vertical',
                               style='Tasks.Vertical.TScrollbar',
                               command=self.display.yview)
        scroll.grid(row=2, column=1, sticky='ns', pady=(2, 16))
        self.display.configure(yscrollcommand=scroll.set)
        self.display_tasks()

        corner = Sizegrip(self, style="Tasks.TSizegrip")
        corner.place(relx=1, rely=1, anchor='se')

        geometry = CONFIG.get('Tasks', 'geometry')
        self.update_idletasks()
        if geometry:
            self.geometry(geometry)
            if self.display.get('1.0', 'end') != '\n':
                self.deiconify()
                self.variable.set(True)

        # --- bindings
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        label.bind('<ButtonPress-1>', self._start_move)
        label.bind('<ButtonRelease-1>', self._stop_move)
        label.bind('<B1-Motion>', self._move)
        self.bind('<Configure>', self._on_configure)
        self.display.bind('<Unmap>', self._on_unmap)
        self.display.bind('<Map>', self._on_map)

    def _on_map(self, event=None):
        ''' make widget sticky '''
        try:
            pos = self._position.get()
            if pos == 'above':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.tasks':
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            elif pos == 'below':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.tasks':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            else:
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.tasks':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            self.ewmh.display.flush()
            self.variable.set(True)
            save_config()
        except TypeError:
            pass

    def _on_unmap(self, event):
        CONFIG.set('Tasks', 'geometry', '')
        self.variable.set(False)

    def _on_configure(self, event):
        CONFIG.set('Tasks', 'geometry', self.geometry())
        save_config()

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

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y
        self.configure(cursor='fleur')
        self.display.configure(cursor='fleur')

    def _stop_move(self, event):
        self.x = None
        self.y = None
        self.configure(cursor='arrow')
        self.display.configure(cursor='arrow')

    def _move(self, event):
        if self.x is not None and self.y is not None:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry("+%s+%s" % (x, y))
