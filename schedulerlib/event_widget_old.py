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


Event desktop widget
"""

from tkinter import Toplevel, Text, BooleanVar, Menu, StringVar
from tkinter.ttk import Style, Label, Separator, Sizegrip
from schedulerlib.constants import CONFIG
from ewmh import EWMH
from datetime import datetime, timedelta


class EventWidget(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.attributes('-type', 'splash')
        self.attributes('-alpha', CONFIG.get('General', 'alpha'))
        self.minsize(50, 50)

        self._position = StringVar(self, CONFIG.get('Events', 'position'))
        self._position.trace_add('write', lambda *x: CONFIG.set('Events', 'position', self._position.get()))

        self.ewmh = EWMH()
        self.title('scheduler.events')
        self.withdraw()

        # control main menu checkbutton
        self.variable = BooleanVar(self, False)

        # --- style
        bg = CONFIG.get('Events', 'background')
        fg = CONFIG.get('Events', 'foreground')
        self.configure(bg=bg)

        style = Style(self)
        style.configure('events.TFrame', background=bg)
        style.configure('events.TSizegrip', background=bg)
        style.configure('events.TSeparator', background=bg)
        style.configure('events.TLabel', background=bg, foreground=fg)

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
        Label(self, text='EVENTS', style='events.TLabel',
              font=CONFIG.get('Events', 'font_title')).pack(pady=4)
        Separator(self, style='events.TSeparator').pack(fill='x')
        self.display = Text(self, width=20, height=10, relief='flat',
                            cursor='arrow', wrap='word',
                            highlightthickness=0, state='disabled',
                            selectbackground=bg,
                            inactiveselectbackground=bg,
                            selectforeground=fg,
                            background=bg, foreground=fg,
                            font=CONFIG.get('Events', 'font'))
        self.display.tag_configure('day', spacing1=5,
                                   font=CONFIG.get('Events', 'font_day'))
        self.display.pack(fill='both', expand=True, padx=2, pady=2)
        self.display_evts()

        corner = Sizegrip(self, style="events.TSizegrip")
        corner.place(relx=1, rely=1, anchor='se')

        geometry = CONFIG.get('Events', 'geometry')
        self.update_idletasks()
        if geometry:
            self.geometry(geometry)
            if self.display.get('1.0', 'end') != '\n':
                self.deiconify()

        # --- bindings
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.bind('<ButtonPress-1>', self._start_move)
        self.bind('<ButtonRelease-1>', self._stop_move)
        self.bind('<B1-Motion>', self._move)
        self.bind('<Configure>', self._on_configure)
        self.display.bind('<Unmap>', self._on_unmap)
        self.display.bind('<Map>', self._on_map)

        # --- update tasks every day
        d = datetime.now()
        d2 = d.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        dt = d2 - d
        self.after(dt.microseconds + 2, self.update_evts)

    def _on_map(self, event=None):
        ''' make widget sticky '''
        for w in self.ewmh.getClientList():
            if w.get_wm_name() == 'scheduler.events':
                self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
        pos = self._position.get()
        if pos == 'above':
            for w in self.ewmh.getClientList():
                if w.get_wm_name() == 'scheduler.events':
                    self.ewmh.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                    self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
        elif pos == 'below':
            for w in self.ewmh.getClientList():
                if w.get_wm_name() == 'scheduler.events':
                    self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                    self.ewmh.setWmState(w, 1, '_NET_WM_STATE_BELOW')
        else:
            for w in self.ewmh.getClientList():
                if w.get_wm_name() == 'scheduler.events':
                    self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                    self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
        self.ewmh.display.flush()
        self.variable.set(True)

    def _on_unmap(self, event):
        CONFIG.set('Events', 'geometry', '')
        self.variable.set(False)

    def _on_configure(self, event):
        CONFIG.set('Events', 'geometry', self.geometry())

    def update_evts(self):
        """ update event list every day"""
        self.display_evts()
        self.after(24*60*60*1000, self.update_evts)

    def display_evts(self):
        week = self.master.get_next_week_events()
#        evts.sort(key=lambda ev: ev['Start'])
        date_today = datetime.now().date()
        today = date_today.strftime('%A')
#        days = []
        self.display.configure(state='normal')
        self.display.delete('1.0', 'end')
#        for ev in evts:
#            day = ev['Start'].strftime('%A')
#            if not day in days:
#                days.append(day)
#                if day == today:
#                    self.display.insert('end', 'Today', ('day',))
#                else:
#                    self.display.insert('end', day.capitalize(), ('day',))
#                self.display.insert('end', '\n')
#
#            if ev["WholeDay"]:
#                if ev['Start'].date() == ev['End'].date():
#                    date = ""
#                else:
#                    start = ev['Start'].strftime('%x')
#                    end = ev['End'].strftime('%x')
#                    date = "%s - %s " % (start, end)
#            else:
#                if ev['Start'].date() == ev['End'].date():
#                    start = ev['Start'].strftime('%H:%M')
#                    end = ev['End'].strftime('%H:%M')
#                else:
#                    start = ev['Start'].strftime('%x %H:%M')
#                    end = ev['End'].strftime('%x %H:%M')
#                date = "%s - %s " % (start, end)
#
#            place = "(%s)" % ev['Place']
#            if place == "()":
#                place = ""
#
#            txt = "%s%s %s\n" % (date, ev['Summary'], place)
#
#            self.display.insert('end', txt)
        for day, evts in week.items():
            if day == today:
                self.display.insert('end', 'Today', ('day',))
            else:
                self.display.insert('end', day.capitalize(), ('day',))
            self.display.insert('end', '\n')
            self.display.insert('end', ''.join([e[0] for e in evts]))
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
