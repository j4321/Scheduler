#!/usr/bin/env python3
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


Tooltip and wrapper
"""


from tkinter import Toplevel
from tkinter.ttk import Label, Style
from tkinter.font import Font


class Tooltip(Toplevel):
    """ Tooltip class """
    def __init__(self, parent, **kwargs):
        """
            Create a tooltip with given parent.

            KEYWORD OPTIONS

                title, alpha, padx, pady, font, background, foreground, image, text

        """
        Toplevel.__init__(self, parent)
        if 'title' in kwargs:
            self.title(kwargs['title'])
        self.transient(parent)
        self.attributes('-type', 'tooltip')
        self.attributes('-alpha', kwargs.get('alpha', 0.75))
        self.overrideredirect(True)
        self.configure(padx=kwargs.get('padx', 4))
        self.configure(pady=kwargs.get('pady', 4))

        self.font = Font(self, kwargs.get('font', ''))

        self.style = Style(self)
        if 'background' in kwargs:
            bg = kwargs['background']
            self.configure(background=bg)
            self.style.configure('tooltip.TLabel', background=bg)
        if 'foreground' in kwargs:
            self.style.configure('tooltip.TLabel', foreground=kwargs['foreground'])

        self.im = kwargs.get('image', None)
        self.label = Label(self, text=kwargs.get('text', ''), image=self.im,
                           style='tooltip.TLabel', font=self.font,
                           wraplength='6c',
                           compound=kwargs.get('compound', 'left'))
        self.label.pack()

    def configure(self, **kwargs):
        if 'text' in kwargs:
            self.label.configure(text=kwargs.pop('text'))
        if 'image' in kwargs:
            self.label.configure(image=kwargs.pop('image'))
        if 'background' in kwargs:
            self.style.configure('tooltip.TLabel', background=kwargs['background'])
        if 'foreground' in kwargs:
            fg = kwargs.pop('foreground')
            self.style.configure('tooltip.TLabel', foreground=fg)
        if 'alpha' in kwargs:
            self.attributes('-alpha', kwargs.pop('alpha'))
        if 'font' in kwargs:
            font = Font(self, kwargs.pop('font'))
            self.font.configure(**font.actual())
        Toplevel.configure(self, **kwargs)

    def config(self, **kw):
        self.configurere(**kw)

    def cget(self, key):
        if key in ['text', 'image']:
            return self.label.cget(key)
        elif key == 'font':
            return self.font
        elif key == 'alpha':
            return self.attributes('-alpha')
        elif key in ['foreground', 'background']:
            return self.style.lookup('tooltip.TLabel', key)
        else:
            return Toplevel.cget(self, key)


class TooltipWrapper:
    """ TooltipWrapper class. """
    def __init__(self, widget, **kwargs):
        """
            Create a tooltip and all the bindings so that it appears
            when the mouse stays over the widget longer than the given delay.

            KEYWORD OPTIONS

                delay and all the options accepted by Tooltip
        """
        self.widget = widget
        if 'delay' in kwargs:
            self.delay = kwargs.pop('delay')
        else:
            self.delay = 1000
        self._timer_id = None
        self.tooltip = Tooltip(self.widget, **kwargs)
        self.tooltip.withdraw()

        i1 = self.widget.bind('<Enter>', self._on_enter, True)
        i2 = self.widget.bind('<Leave>', self._on_leave, True)
        i3 = self.tooltip.bind('<Leave>', self._on_leave_tooltip)
        i4 = self.tooltip.bind("<FocusOut>", lambda e: self.tooltip.withdraw())
        self._bind_ids = [i1, i2, i3, i4]

    def _on_enter(self, event):
        if not self.tooltip.winfo_ismapped():
            self._timer_id = self.widget.after(self.delay, self.display_tooltip)

    def _on_leave(self, event):
        if self.tooltip.winfo_ismapped():
            x, y = self.widget.winfo_pointerxy()
            if not self.widget.winfo_containing(x, y) in [self.widget, self.tooltip]:
                self.tooltip.withdraw()
        else:
            self.widget.after_cancel(self._timer_id)

    def _on_leave_tooltip(self, event):
        x, y = self.widget.winfo_pointerxy()
        if not self.widget.winfo_containing(x, y) in [self.widget, self.tooltip]:
            self.tooltip.withdraw()

    def display_tooltip(self):
        self.tooltip.deiconify()
        x = self.widget.winfo_pointerx() + 14
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tooltip.geometry('+%i+%i' % (x, y))
        self.tooltip.focus_set()

    def destroy(self):
        self.widget.unbind('<Enter>', self._bind_ids[0])
        self.widget.unbind('<Leave>', self._bind_ids[1])
        self.tooltip.unbind('<Leave>', self._bind_ids[2])
        self.tooltip.unbind('<FocusOut>', self._bind_ids[3])
        self.tooltip.destroy()

    def configure(self, **kw):
        delay = kw.pop('delay', None)
        if delay is not None:
            self.delay = int(delay)
        self.tooltip.configure(**kw)

    def cget(self, key):
        if key == 'delay':
            return self.delay
        else:
            return self.tooltip.cget(key)

