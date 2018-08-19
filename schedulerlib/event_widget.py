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

from tkinter import Toplevel, BooleanVar, Menu, StringVar, PhotoImage, Canvas
from tkinter.ttk import Style, Label, Separator, Sizegrip, Frame, Checkbutton
from schedulerlib.constants import CONFIG, CLOSED, OPENED, CLOSED_SEL, OPENED_SEL, save_config
from schedulerlib.ttkwidgets import AutoScrollbar
from ewmh import EWMH
from datetime import datetime, timedelta


class ToggledFrame(Frame):
    """
    A frame that can be toggled to open and close
    """

    def __init__(self, master=None, text="", **kwargs):
        Frame.__init__(self, master, **kwargs)
        style_name = self.cget('style')
        toggle_style_name = '%s.Toggle' % ('.'.join(style_name.split('.')[:-1]))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        style = Style(self)
        if "toggle" not in style.element_names():
            self._open_image = PhotoImage('img_opened', file=OPENED, master=self)
            self._closed_image = PhotoImage('img_closed', file=CLOSED, master=self)
            self._open_image_sel = PhotoImage('img_opened_sel', file=OPENED_SEL, master=self)
            self._closed_image_sel = PhotoImage('img_closed_sel', file=CLOSED_SEL, master=self)
            style.element_create("toggle", "image", "img_closed",
                                 ("selected", "!disabled", "img_opened"),
                                 ("active", "!selected", "!disabled", "img_closed_sel"),
                                 ("active", "selected", "!disabled", "img_opened_sel"),
                                 border=2, sticky='')
            style.configure(toggle_style_name,
                            background=style.lookup(style_name, 'background'))
            style.map(toggle_style_name, background=[])
            style.layout('Toggle',
                         [('Toggle.border',
                           {'children': [('Toggle.padding',
                                          {'children': [('Toggle.toggle',
                                                         {'sticky': 'nswe'})],
                                           'sticky': 'nswe'})],
                            'sticky': 'nswe'})])
        self.__checkbutton = Checkbutton(self,
                                         style=toggle_style_name,
                                         command=self.toggle,
                                         cursor='arrow')
        self.label = Label(self, text=text,
                           style=style_name.replace('TFrame', 'TLabel'))
        self.interior = Frame(self, style=style_name)
        self.label.bind('<Configure>', self._wrap)
        self._grid_widgets()

    def _wrap(self, event):
        self.label.configure(wraplength=self.label.winfo_width())

    def _grid_widgets(self):
        self.__checkbutton.grid(row=0, column=0)
        self.label.grid(row=0, column=1, sticky="we")

    def toggle(self):
        if 'selected' not in self.__checkbutton.state():
            self.interior.grid_forget()
        else:
            self.interior.grid(row=1, column=1, sticky="nswe", padx=(4, 0))


class EventWidget(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.attributes('-type', 'splash')
        self.attributes('-alpha', CONFIG.get('General', 'alpha'))
        self.minsize(50, 50)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

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
        style.configure('Events.TFrame', background=bg)
        style.configure('Events.TSizegrip', background=bg)
        style.configure('Events.TSeparator', background=bg)
        style.configure('Events.TLabel', background=bg, foreground=fg)

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
        label = Label(self, text='EVENTS', style='Events.TLabel',
                      anchor='center',font=CONFIG.get('Events', 'font_title'))
        label.grid(row=0, columnspan=2, pady=4, sticky='ew')
        Separator(self, style='Events.TSeparator').grid(row=1, columnspan=2, sticky='we')
        self.canvas = Canvas(self, background=bg, highlightthickness=0)
        self.canvas.grid(sticky='nsew', row=2, column=0, padx=2, pady=2)
        scroll = AutoScrollbar(self, orient='vertical',
                               style='Events.Vertical.TScrollbar',
                               command=self.canvas.yview)
        scroll.grid(row=2, column=1, sticky='ns', pady=(2, 16))
        self.canvas.configure(yscrollcommand=scroll.set)

        self.display = Frame(self.canvas, style='Events.TFrame')
        self.canvas.create_window(0, 0, anchor='nw', window=self.display, tags=('display',))
#        self.display = Text(self, width=20, height=10, relief='flat',
#                            cursor='arrow', wrap='word',
#                            highlightthickness=0, state='disabled',
#                            selectbackground=bg,
#                            inactiveselectbackground=bg,
#                            selectforeground=fg,
#                            background=bg, foreground=fg,
#                            font=CONFIG.get('Events', 'font'))
#        self.display.tag_configure('day', spacing1=5,
#                                   font=CONFIG.get('Events', 'font_day'))
        self.display.columnconfigure(0, weight=1)
        self.display_evts()

        corner = Sizegrip(self, style="Events.TSizegrip")
        corner.place(relx=1, rely=1, anchor='se')

        geometry = CONFIG.get('Events', 'geometry')
        self.update_idletasks()
        if geometry:
            self.geometry(geometry)
            if self.display.children:
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
        self.bind('<4>', lambda e: self._scroll(-1))
        self.bind('<5>', lambda e: self._scroll(1))

        # --- update tasks every day
        d = datetime.now()
        d2 = d.replace(hour=0, minute=0, second=1, microsecond=0) + timedelta(days=1)
        dt = d2 - d
        self.after(int(dt.total_seconds() * 1e3), self.update_evts)

        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _scroll(self, delta):
        top, bottom = self.canvas.yview()
        top += delta * 0.05
        top = min(max(top, 0), 1)
        self.canvas.yview_moveto(top)

    def _on_map(self, event=None):
        ''' make widget sticky '''
        try:
            pos = self._position.get()
            if pos == 'above':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.events':
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            elif pos == 'below':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.events':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            else:
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.events':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            self.ewmh.display.flush()
            self.variable.set(True)
            save_config()
        except TypeError:
            pass

    def _on_unmap(self, event):
        CONFIG.set('Events', 'geometry', '')
        self.variable.set(False)

    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.itemconfigure('display', width=self.canvas.winfo_width() - 4)
        CONFIG.set('Events', 'geometry', self.geometry())
        save_config()

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
                text = 'Today'
            else:
                text = day.capitalize()
            Label(self.display, text=text,
                  font=CONFIG.get('Events', 'font_day'),
                  style='Events.TLabel').grid(sticky='w', pady=(4, 0), padx=4)
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
