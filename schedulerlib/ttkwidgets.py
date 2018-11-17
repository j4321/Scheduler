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


Miscellaneous tkinter widgets.
"""


from tkinter.ttk import Scrollbar, Frame, Label, Checkbutton


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


class LabelFrame(Frame):
    """ LabelFrame with the text hiding part of the border
        (which is not the case for the ususal LabelFrame in clam theme. """
    def __init__(self, master=None, **kw):
        kw['relief'] = 'groove'
        kw['borderwidth'] = 1
        text = kw.pop('text', '')
        Frame.__init__(self, master, **kw)
        self._label = Label(master, text=text)
        self._label.place(in_=self, relx=0.5, y=0, anchor='n',
                          bordermode='outside')
        self._label.bind('<Map>', self._update)
        self._layout = None

    def configure(self, **kw):
        text = kw.pop('text', None)
        if text is not None:
            self._label.configure(text=text)
            self._update()
        Frame.configure(self, **kw)

    def _update(self, event=None):
        h = self._label.winfo_height()
        self._label.place_configure(y=-int(h * 0.5))
        self.configure(padding=h // 2)

        if self._layout == 'pack':
            pady = self.pack_info()['pady']
        elif self._layout == 'grid':
            pady = self.grid_info()['pady']

        if type(pady) is tuple:
            pady = (pady[0] + h // 2, pady[1])
        else:
            pady = (pady + h // 2, pady)

        if self._layout == 'grid':
            Frame.grid_configure(self, pady=pady)
        elif self._layout == 'pack':
            Frame.pack_configure(self, pady=pady)

    def config(self, **kw):
        self.configure(**kw)

    def cget(self, key):
        if key == 'text':
            return self._label.cget('text')
        else:
            return Frame.cget(self, key)

    def pack(self, **kw):
        h = self._label.winfo_height()
        pady = kw.pop('pady', 0)
        self._layout = 'pack'
        if type(pady) is tuple:
            pady = (pady[0] + h // 2, pady[1])
        else:
            pady = (pady + h // 2, pady)
        Frame.pack(self, pady=pady)

    def pack_forget(self):
        Frame.pack_forget(self)
        self._layout = None

    def grid_forget(self):
        Frame.grid_forget(self)
        self._layout = None

    def grid_remove(self):
        Frame.grid_remove(self)
        self._layout = None

    def grid(self, **kw):
        h = self._label.winfo_height()
        pady = kw.pop('pady', 0)
        self._layout = 'grid'
        if type(pady) is tuple:
            pady = (pady[0] + h // 2, pady[1])
        else:
            pady = (pady + h // 2, pady)
        Frame.grid(self, pady=pady, **kw)

    def __getitem__(self, item):
        return self.cget(item)

    def __setitem__(self, item, value):
        self.configure(item=value)


class AutoScrollbar(Scrollbar):
    """ Scrollbar that automatically vanishes when not needed """
    def __init__(self, *args, **kwargs):
        Scrollbar.__init__(self, *args, **kwargs)
        self._pack_kw = {}
        self._place_kw = {}
        self._layout = 'place'

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            if self._layout == 'place':
                self.place_forget()
            elif self._layout == 'pack':
                self.pack_forget()
            else:
                self.grid_remove()
        else:
            if self._layout == 'place':
                self.place(**self._place_kw)
            elif self._layout == 'pack':
                self.pack(**self._pack_kw)
            else:
                self.grid()
        Scrollbar.set(self, lo, hi)

    def place(self, **kw):
        Scrollbar.place(self, **kw)
        self._place_kw = self.place_info()
        self._layout = 'place'

    def pack(self, **kw):
        Scrollbar.pack(self, **kw)
        self._pack_kw = self.pack_info()
        self._layout = 'pack'

    def grid(self, **kw):
        Scrollbar.grid(self, **kw)
        self._layout = 'grid'
