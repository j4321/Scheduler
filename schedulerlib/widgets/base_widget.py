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


Base desktop widget class
"""


from tkinter import Toplevel, BooleanVar, StringVar, Menu
from tkinter.ttk import Style
from schedulerlib.constants import CONFIG, save_config, active_color
from ewmh import EWMH


class BaseWidget(Toplevel):

    def __init__(self, name, master=None, **kw):
        """
        Create a  desktop widget that sticks on the desktop.
        """
        Toplevel.__init__(self, master)
        self.name = name
        self.attributes('-type', 'splash')

        self.style = Style(self)

        self._position = StringVar(self, CONFIG.get(self.name, 'position'))
        self._position.trace_add('write', lambda *x: CONFIG.set(self.name, 'position', self._position.get()))

        self.ewmh = EWMH()
        self.title('scheduler.{}'.format(self.name.lower()))

        self.withdraw()

        # control main menu checkbutton
        self.variable = BooleanVar(self, False)

        # --- menu
        self.menu = Menu(self, relief='sunken', activeborderwidth=0)
        self._populate_menu()

        self.create_content(**kw)

        self.x = None
        self.y = None

        if CONFIG.getboolean(self.name, 'visible', fallback=True):
            self.show()

        # --- geometry
        geometry = CONFIG.get(self.name, 'geometry')
        self.update_idletasks()
        if geometry:
            self.geometry(geometry)

        # --- bindings
        self.bind('<Configure>', self._on_configure)

    def create_content(self):
        # to be overriden by subclass
        pass

    def _populate_menu(self):
        self.menu_pos = Menu(self.menu, relief='sunken', activeborderwidth=0)
        self.menu_pos.add_radiobutton(label='Normal', value='normal',
                                      variable=self._position, command=self.show)
        self.menu_pos.add_radiobutton(label='Above', value='above',
                                      variable=self._position, command=self.show)
        self.menu_pos.add_radiobutton(label='Below', value='below',
                                      variable=self._position, command=self.show)
        self.menu.add_cascade(label='Position', menu=self.menu_pos)
        self.menu.add_command(label='Hide', command=self.hide)

    def update_style(self):
        bg = CONFIG.get(self.name, 'background', fallback='grey10')
        fg = CONFIG.get(self.name, 'foreground', fallback='white')
        active_bg = active_color(*self.winfo_rgb(bg))
        self.attributes('-alpha', CONFIG.get(self.name, 'alpha', fallback=0.85))
        self.configure(bg=bg)
        self.menu.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                            activebackground=active_bg)
        self.menu_pos.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                                activebackground=active_bg)

    def _on_configure(self, event):
        CONFIG.set(self.name, 'geometry', self.geometry())
        save_config()

    def hide(self):
        CONFIG.set(self.name, 'visible', 'False')
        self.variable.set(False)
        save_config()
        self.withdraw()

    def show(self):
        ''' make widget sticky '''
        self.deiconify()
        self.update_idletasks()
        try:
            pos = self._position.get()
            for w in self.ewmh.getClientList():
                if w.get_wm_name() == self.title():
                    if pos == 'above':
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
                    elif pos == 'below':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
                    else:
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            self.ewmh.display.flush()
            CONFIG.set(self.name, 'visible', 'True')
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
