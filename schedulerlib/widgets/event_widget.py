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
from tkinter import Canvas, Menu, BooleanVar
from tkinter.ttk import Label, Separator, Sizegrip, Frame
from datetime import datetime

from schedulerlib.constants import CONFIG, active_color, save_config
from schedulerlib.ttkwidgets import AutoScrollbar, ToggledFrame
from .base_widget import BaseWidget


class EventWidget(BaseWidget):
    def __init__(self, master):
        self._cat_var = {}
        BaseWidget.__init__(self, 'Events', master)

    def create_content(self):
        """Create widget's GUI."""
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
        self.display.columnconfigure(0, weight=1)
        self.canvas.create_window(0, 0, anchor='nw', window=self.display, tags=('display',))

        corner = Sizegrip(self, style="Events.TSizegrip")
        corner.place(relx=1, rely=1, anchor='se')

        # --- bindings
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        label.bind('<ButtonPress-1>', self._start_move)
        label.bind('<ButtonRelease-1>', self._stop_move)
        label.bind('<B1-Motion>', self._move)
        self.bind('<4>', lambda e: self._scroll(-1))
        self.bind('<5>', lambda e: self._scroll(1))

        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _populate_menu(self):
        """Create menu."""
        BaseWidget._populate_menu(self)
        self.menu.add_separator()
        self.menu_cat = Menu(self.menu, tearoff=False)
        self.menu_cat.add_command(label=_('Select all'), command=self.display_all_cats)
        self.menu_cat.add_command(label=_('Unselect all'), command=self.hide_all_cats)
        self.menu_cat.add_separator()
        self.menu.add_cascade(label=_('Display categories'), menu=self.menu_cat)

    def display_all_cats(self):
        for var in self._cat_var.values():
            var.set(True)
        self.display_evts()

    def hide_all_cats(self):
        for var in self._cat_var.values():
            var.set(False)
        self.display_evts()

    def update_style(self):
        """Update widget's style."""
        BaseWidget.update_style(self)
        bg = CONFIG.get('Events', 'background')
        fg = CONFIG.get('Events', 'foreground')
        active_bg = active_color(*self.winfo_rgb(bg))
        self.attributes('-alpha', CONFIG.get(self.name, 'alpha'))
        self.configure(bg=bg)
        self.menu_cat.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                                activebackground=active_bg)

        self.style.configure('day.Events.TLabel',
                             font=CONFIG.get('Events', 'font_day'))
        self.style.configure('Toggle', background=bg)
        self.canvas.configure(bg=bg)
        for cat in list(self._cat_var.keys()):
            if not CONFIG.has_option('Categories', cat):
                del self._cat_var[cat]
                self.menu_cat.delete(cat)
        displayed_cats = CONFIG.get('Events', 'categories').split(', ')
        for cat, val in CONFIG.items('Categories'):
            if cat not in self._cat_var:
                self._cat_var[cat] = BooleanVar(self, cat in displayed_cats)
                self.menu_cat.add_checkbutton(label=cat,
                                              variable=self._cat_var[cat],
                                              command=self.display_evts)
            props = val.split(', ')
            self.style.configure(f'ev_{cat}.Events.TFrame',
                                 background=props[1], foreground=props[0])
        self.display_evts()

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

    def display_evts(self):

        def wrap(event):
            l = event.widget
            if l.master.winfo_ismapped():
                l.configure(wraplength=l.winfo_width() - 4)

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
            for ev, desc, cat in evts:
                if not self._cat_var[cat].get():
                    continue
                if desc.strip():
                    tf = ToggledFrame(self.display, text=ev.strip(), category=cat,
                                      style='Events.TFrame')
                    l = Label(tf.interior,
                              text=desc.strip(),
                              style='Events.TLabel')
                    l.pack(padx=4, fill='both', expand=True)
                    l.configure(wraplength=l.winfo_width())
                    l.bind('<Configure>', wrap)
                    tf.grid(sticky='we', pady=2, padx=(8, 4))
                else:
                    frame = Frame(self.display, style='Events.TFrame')
                    Frame(frame, style=f'ev_{cat}.Events.TFrame', width=10,
                          height=10).pack(side='left', padx=(0, 2))
                    l = Label(frame, text=ev.strip(),
                              style='Events.TLabel')
                    l.bind('<Configure>', wrap)
                    l.pack(side='left', fill='x', expand=True)
                    frame.grid(sticky='ew', pady=2, padx=(21, 10))

        displayed_cat = [cat for cat, var in self._cat_var.items() if var.get()]
        CONFIG.set('Events', 'categories', ', '.join(displayed_cat))
        save_config()
