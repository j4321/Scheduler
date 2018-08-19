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


Calendar desktop widget
"""


from tkinter import Toplevel, BooleanVar, StringVar, Menu
from schedulerlib.constants import CONFIG
from schedulerlib.event_calendar import EventCalendar
from ewmh import EWMH


class CalendarWidget(Toplevel):

    def __init__(self, master=None, **kw):
        """
        Create a CalendarWidget that sticks on the desktop.

        OPTIONS

            the same as EventCalendar

        """
        Toplevel.__init__(self, master)
        self.attributes('-type', 'splash')

        self._position = StringVar(self, CONFIG.get('Calendar', 'position'))
        self._position.trace_add('write', lambda *x: CONFIG.set('Calendar', 'position', self._position.get()))

        self.ewmh = EWMH()
        self.title('scheduler.calendar')
        self.withdraw()

        # control main menu checkbutton
        self.variable = BooleanVar(self, False)

        # --- options
        self.attributes('-alpha', CONFIG.get('General', 'alpha'))
        bg = kw.get('background', '#424242')
        self.configure(bg=bg)

        self._calendar = EventCalendar(self, **kw)
        self._calendar.pack(padx=1, pady=1)

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

        # --- events
        for ev in self.master.events.values():
            self._calendar.add_event(ev)

        geometry = CONFIG.get('Calendar', 'geometry')
        self.update_idletasks()
        if geometry:
            self.geometry(geometry)
            self.deiconify()

        # --- bindings
        self._calendar.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.bind('<ButtonPress-1>', self._start_move)
        self.bind('<ButtonRelease-1>', self._stop_move)
        self.bind('<B1-Motion>', self._move)
        self.bind('<Configure>', self._on_configure)
        self.bind('<Map>', self._on_map)
        self.bind('<Unmap>', self._on_unmap)

    # --- bindings
    def _on_configure(self, event):
        geo = self.geometry().split('+')[1:]
        CONFIG.set('Calendar', 'geometry', '+%s+%s' % tuple(geo))
        self.variable.set(True)

    def _on_unmap(self, event):
        CONFIG.set('Calendar', 'geometry', '')
        self.variable.set(False)

    def _on_map(self, event=None):
        ''' make widget sticky '''
        try:
            pos = self._position.get()
            if pos == 'above':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.calendar':
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            elif pos == 'below':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.calendar':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            else:
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.calendar':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            self.ewmh.display.flush()
            self.variable.set(True)
            save_config()
        except TypeError:
            pass

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _stop_move(self, event):
        self.x = None
        self.y = None
        self.configure(cursor='arrow')

    def _move(self, event):
        if self.x is not None and self.y is not None:
            self.configure(cursor='fleur')
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry("+%s+%s" % (x, y))

    # --- public methods
    def add_event(self, event):
        self._calendar.add_event(event)

    def remove_event(self, event):
        self._calendar.remove_event(event)

    def get_events(self, date):
        return self._calendar.get_events(date)
