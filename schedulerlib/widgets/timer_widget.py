#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 13:02:41 2017

@author: juliette
"""

from tkinter import Text
from tkinter.ttk import Button, Label, Sizegrip
from schedulerlib.constants import IM_PLAY, IM_PAUSE, STOP, CONFIG, active_color
from .base_widget import BaseWidget
from PIL.ImageTk import PhotoImage


class Timer(BaseWidget):
    def __init__(self, master):
        BaseWidget.__init__(self, 'Timer', master)

    def create_content(self, **kw):
        self.minsize(50, 120)

        self._time = [0, 0, 0]
        self._on = False
        self._after_id = ''

        self.img_play = PhotoImage(master=self, file=IM_PLAY)
        self.img_pause = PhotoImage(master=self, file=IM_PAUSE)
        self.img_stop = PhotoImage(master=self, file=STOP)

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # --- GUI elements
        self.display = Label(self, text='%i:%.2i:%.2i' % tuple(self._time),
                             anchor='center',
                             style='timer.TLabel')
        self.intervals = Text(self, highlightthickness=0, relief='flat',
                              height=3, width=1,
                              inactiveselectbackground=self.style.lookup('TEntry', 'selectbackground'))
        self.intervals.tag_configure('center', justify='center')
        self.intervals.configure(state='disabled')
        self.b_interv = Button(self, text=_('Interval'), style='timer.TButton',
                               command=self.add_interval)
        self.b_interv.state(('disabled',))

        self.b_launch = Button(self, image=self.img_play, padding=2,
                               command=self.launch, style='timer.TButton')
        self.b_stop = Button(self, image=self.img_stop, padding=2,
                             command=self.stop, style='timer.TButton')

        # --- placement
        self.display.grid(row=0, columnspan=2, sticky='ew', padx=8, pady=(4, 0))
        Label(self, text=_('Intervals:'),
              style='timer.TLabel').grid(row=1, columnspan=2, sticky='w', padx=4)
        self.intervals.grid(row=2, columnspan=2, sticky='eswn')
        self.b_interv.grid(row=3, columnspan=2, sticky='ew')
        self.b_launch.grid(row=4, column=0, sticky='ew')
        self.b_stop.grid(row=4, column=1, sticky='ew')

        self._corner = Sizegrip(self, style="timer.TSizegrip")
        self._corner.place(relx=1, rely=1, anchor='se')

        # --- bindings
        self.intervals.bind("<1>", lambda event: self.intervals.focus_set())
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.display.bind('<ButtonPress-1>', self._start_move)
        self.display.bind('<ButtonRelease-1>', self._stop_move)
        self.display.bind('<B1-Motion>', self._move)
        self.b_stop.bind('<Enter>', self._on_enter)
        self.b_stop.bind('<Leave>', self._on_leave)

    def update_style(self):
        self.attributes('-alpha', CONFIG.get(self.name, 'alpha', fallback=0.85))
        bg = CONFIG.get('Timer', 'background')
        fg = CONFIG.get('Timer', 'foreground')
        active_bg = active_color(*self.winfo_rgb(bg))
        self.configure(bg=bg)
        self.menu.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                            activebackground=active_bg)
        self.menu_pos.configure(bg=bg, fg=fg, selectcolor=fg, activeforeground=fg,
                                activebackground=active_bg)
        self.display.configure(font=CONFIG.get('Timer', 'font_time'))
        self.intervals.configure(bg=bg, fg=fg,
                                 font=CONFIG.get('Timer', 'font_intervals'))
        self.style.configure('timer.TButton', background=bg, relief='flat',
                             foreground=fg, borderwidth=0)
        self.style.configure('timer.TLabel', background=bg,
                             foreground=fg)
        self.style.configure('timer.TSizegrip', background=bg)
        self.style.map('timer.TSizegrip', background=[('active', active_bg)])
        self.style.map('timer.TButton', background=[('disabled', bg),
                                                    ('!disabled', 'active', active_bg)])

    def _on_enter(self, event=None):
        self._corner.state(('active',))

    def _on_leave(self, event=None):
        self._corner.state(('!active',))

    def show(self):
        self.withdraw()
        if self._position.get() == 'above':
            self.overrideredirect(True)
        else:
            self.overrideredirect(False)
        BaseWidget.show(self)

    def _run(self):
        if self._on:
            self._time[2] += 1
            if self._time[2] == 60:
                self._time[2] = 0
                self._time[1] += 1
                if self._time[1] == 60:
                    self._time[1] = 0
                    self._time[0] += 1
            self.display.configure(text='%i:%.2i:%.2i' % tuple(self._time))
            self._after_id = self.after(1000, self._run)

    def launch(self):
        if self._on:
            self._on = False
            self.b_launch.configure(image=self.img_play)
            self.b_interv.state(('disabled',))
        else:
            self._on = True
            self.b_interv.state(('!disabled',))
            self.b_launch.configure(image=self.img_pause)
            self.after(1000, self._run)

    def add_interval(self):
        tps = '\n%i:%.2i:%.2i' % tuple(self._time)
        if self.intervals.get('1.0', 'end') == '\n':
            tps = tps[1:]
        self.intervals.configure(state='normal')
        self.intervals.insert('end', tps, 'center')
        self.intervals.configure(state='disabled')

    def stop(self):
        self._on = False
        self.b_interv.state(('disabled',))
        self.b_launch.configure(image=self.img_play)
        self._time = [0, 0, 0]
        self.intervals.configure(state='normal')
        self.intervals.delete('1.0', 'end')
        self.intervals.configure(state='disabled')
        self.display.configure(text='%i:%.2i:%.2i' % tuple(self._time))
