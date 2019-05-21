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


Event desktop widget
"""
from tkinter import Canvas
from tkinter.ttk import Label, Separator, Sizegrip, Frame
from datetime import datetime, timedelta

from schedulerlib.constants import CONFIG, active_color
from schedulerlib.ttkwidgets import AutoScrollbar, ToggledFrame
from .base_widget import BaseWidget


class EventWidget(BaseWidget):
    def __init__(self, master):
        BaseWidget.__init__(self, 'Events', master)

    def create_content(self, **kw):
        self.minsize(50, 50)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        label = Label(self, text=_('Events').upper(), style='title.Events.TLabel',
                      anchor='center')
        label.grid(row=0, columnspan=2, pady=4, sticky='ew')
        Separator(self, style='Events.TSeparator').grid(row=1, columnspan=2, sticky='we')
        self.canvas = Canvas(self, highlightthickness=0)
        self.canvas.grid(sticky='nsew', row=2, column=0, padx=2, pady=2)
        scroll = AutoScrollbar(self, orient='vertical',
                               style='Events.Vertical.TScrollbar',
                               command=self.canvas.yview)
        scroll.grid(row=2, column=1, sticky='ns', pady=(2, 16))
        self.canvas.configure(yscrollcommand=scroll.set)

        self.display = Frame(self.canvas, style='Events.TFrame')
        self.canvas.create_window(0, 0, anchor='nw', window=self.display, tags=('display',))
        self.display_evts()

        corner = Sizegrip(self, style="Events.TSizegrip")
        corner.place(relx=1, rely=1, anchor='se')

        # --- bindings
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        label.bind('<ButtonPress-1>', self._start_move)
        label.bind('<ButtonRelease-1>', self._stop_move)
        label.bind('<B1-Motion>', self._move)
        self.bind('<4>', lambda e: self._scroll(-1))
        self.bind('<5>', lambda e: self._scroll(1))

        # --- update tasks every day
        d = datetime.now()
        d2 = d.replace(hour=0, minute=0, second=1, microsecond=0) + timedelta(days=1)
        dt = d2 - d
        self.after(int(dt.total_seconds() * 1e3), self.update_evts)

        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def update_style(self):
        bg = CONFIG.get('Events', 'background')
        fg = CONFIG.get('Events', 'foreground')
        active_bg = active_color(*self.winfo_rgb(bg))
        self.attributes('-alpha', CONFIG.get(self.name, 'alpha', fallback=0.85))
        self.style.configure('Events.TFrame', background=bg)
        self.style.configure('Events.TSizegrip', background=bg)
        self.style.configure('Events.TSeparator', background=bg)
        self.style.configure('Events.TLabel', background=bg, foreground=fg,
                             font=CONFIG.get('Events', 'font'))
        self.style.configure('title.Events.TLabel',
                             font=CONFIG.get('Events', 'font_title'))
        self.style.configure('day.Events.TLabel',
                             font=CONFIG.get('Events', 'font_day'))
        self.style.configure('Toggle', background=bg)
        self.configure(bg=bg)
        self.menu_pos.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                                activebackground=active_bg)
        self.menu.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                            activebackground=active_bg)
        self.canvas.configure(bg=bg)

    def _scroll(self, delta):
        top, bottom = self.canvas.yview()
        top += delta * 0.05
        top = min(max(top, 0), 1)
        self.canvas.yview_moveto(top)

    def _on_configure(self, event):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            self.canvas.itemconfigure('display', width=self.canvas.winfo_width() - 4)
        except AttributeError:
            pass  # triggered on start-up before canvas is created
        BaseWidget._on_configure(self, event)

    def update_evts(self):
        """ update event list every day"""
        self.display_evts()
        self.after(24 * 3600 * 1000, self.update_evts)

    def display_evts(self):

        def wrap(event):
            l = event.widget
            if l.master.winfo_ismapped():
                l.configure(wraplength=l.winfo_width())

        week = self.master.get_next_week_events()
        date_today = datetime.now().date()
        today = date_today.strftime('%A')
        children = list(self.display.children.values())
        for ch in children:
            ch.destroy()

        for day, evts in week.items():
            if day == today:
                text = _('Today')
            else:
                text = day.capitalize()
            Label(self.display, text=text,
                  style='day.Events.TLabel').grid(sticky='w', pady=(4, 0), padx=4)
            for ev, desc in evts:
                if desc.strip():
                    tf = ToggledFrame(self.display, text=ev.strip(), style='Events.TFrame')
                    l = Label(tf.interior,
                              text=desc.strip(),
                              style='Events.TLabel')
                    l.pack(padx=4, fill='both', expand=True)
                    l.configure(wraplength=l.winfo_width())
                    l.bind('<Configure>', wrap)
                    tf.grid(sticky='we', pady=2, padx=(8, 4))
                else:
                    l = Label(self.display, text=ev.strip(),
                              style='Events.TLabel')
                    l.bind('<Configure>', wrap)
                    l.grid(sticky='ew', pady=2, padx=(21, 10))
