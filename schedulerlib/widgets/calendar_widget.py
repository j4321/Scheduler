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


Calendar desktop widget
"""


from .base_widget import BaseWidget
from schedulerlib.event_calendar import EventCalendar
from schedulerlib.constants import CONFIG, save_config, active_color


class CalendarWidget(BaseWidget):

    def __init__(self, master=None, **kw):
        """
        Create a CalendarWidget that sticks on the desktop.

        kw: the same as EventCalendar
        """
        BaseWidget.__init__(self, 'Calendar', master, **kw)

    def create_content(self, **kw):
        self._calendar = EventCalendar(self, **kw)
        self._calendar.pack(padx=1, pady=1)
        for ev in self.master.events.values():
            self._calendar.add_event(ev)
        # --- bindings
        self._calendar.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.bind('<ButtonPress-1>', self._start_move)
        self.bind('<ButtonRelease-1>', self._stop_move)
        self.bind('<B1-Motion>', self._move)

    def update_style(self):
        bg = CONFIG.get(self.name, 'background', fallback='grey10')
        fg = CONFIG.get(self.name, 'foreground', fallback='white')
        active_bg = active_color(*self.winfo_rgb(bg))
        self.attributes('-alpha', CONFIG.get(self.name, 'alpha', fallback=0.85))
        self.configure(bg=bg)
        self._calendar.menu.configure(bg=bg, fg=fg, selectcolor=fg,
                                      activeforeground=fg,
                                      activebackground=active_bg)
        self.menu.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                            activebackground=active_bg)
        self.menu_pos.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                                activebackground=active_bg)
        keys = self._calendar.keys()
        opts = {opt: CONFIG.get('Calendar', opt) for opt in CONFIG.options('Calendar') if opt in keys}
        self._calendar.configure(**opts)
        self._calendar['font'] = CONFIG.get('Calendar', 'font')
        self._calendar.update_style()

    def _on_configure(self, event):
        geo = self.geometry().split('+')[1:]
        CONFIG.set(self.name, 'geometry', '+%s+%s' % tuple(geo))
        save_config()

    def update_date(self):
        self._calendar.update_sel()

    def add_event(self, event):
        self._calendar.add_event(event)

    def remove_event(self, event):
        self._calendar.remove_event(event)

    def get_events(self, date):
        return self._calendar.get_events(date)
