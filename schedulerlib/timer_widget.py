#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 13:02:41 2017

@author: juliette
"""

from tkinter import Menu, BooleanVar, StringVar, Toplevel, PhotoImage, Text
from tkinter.ttk import Style, Button, Label, Sizegrip
from ewmh import EWMH
from schedulerlib.constants import PLAY, PAUSE, STOP, CONFIG, active_color, save_config


class Timer(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.attributes('-type', 'splash')
        self.attributes('-alpha', CONFIG.get('General', 'alpha'))
        self.minsize(50, 120)
        self.resizable(False, True)

        # control main menu checkbutton
        self.variable = BooleanVar(self, False)

        self._time = [0, 0, 0]
        self._on = False
        self._after_id = ''
        self._position = StringVar(self, CONFIG.get('Timer', 'position'))
        self._position.trace_add('write', lambda *x: CONFIG.set('Timer', 'position', self._position.get()))

        self.ewmh = EWMH()
        self.title('scheduler.timer')
        self.withdraw()

        self.img_play = PhotoImage(master=self, file=PLAY)
        self.img_pause = PhotoImage(master=self, file=PAUSE)
        self.img_stop = PhotoImage(master=self, file=STOP)

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # --- style
        bg = CONFIG.get('Timer', 'background')
        r, g, b = self.winfo_rgb(bg)
        active_bg = active_color(r*255/65535, g*255/65535, b*255/65535)
        fg = CONFIG.get('Timer', 'foreground')
        self.configure(bg=bg)

        self.style = Style(self)
        self.style.theme_use('clam')
        self.style.configure('timer.TButton', background=bg, relief='flat',
                        foreground=fg, borderwidth=0)
        self.style.configure('timer.TLabel', background=bg,
                        foreground=fg)
        self.style.configure('timer.TSizegrip', background=bg)
        self.style.map('timer.TSizegrip', background=[('active', active_bg)])
#        self.style.configure('close.timer.TButton', font='Latin\ Modern\ Sans 16',)
        self.style.map('timer.TButton', background=[('disabled', bg),
                                               ('!disabled', 'active', active_bg)])
#        self.style.map('close.timer.TButton',
#                  background=[('disabled', bg),
#                              ('!disabled', 'active', bg)],
#                  foreground=[('disabled', fg),
#                              ('!disabled', 'active', 'darkred')])

        # --- menu
        self.menu = Menu(self, tearoff=False)
        menu_pos = Menu(self.menu, tearoff=False)
        menu_pos.add_radiobutton(label='Normal', value='normal',
                                 variable=self._position, command=self._change_pos)
        menu_pos.add_radiobutton(label='Above', value='above',
                                 variable=self._position, command=self._change_pos)
        menu_pos.add_radiobutton(label='Below', value='below',
                                 variable=self._position, command=self._change_pos)
        self.menu.add_cascade(label='Position', menu=menu_pos)
        self.menu.add_command(label='Hide', command=self.withdraw)

        # --- elements
        self.display = Label(self, text='%i:%.2i:%.2i' % tuple(self._time),
                                 anchor='center',
                                 font=CONFIG.get('Timer', 'font_time'),
                                 style='timer.TLabel')
        self.intervals = Text(self, highlightthickness=0, relief='flat', bg=bg,
                              fg=fg, font=CONFIG.get('Timer', 'font_intervals'),
                              height=3, width=1,
                              inactiveselectbackground=self.style.lookup('TEntry', 'selectbackground'))
        self.intervals.tag_configure('center', justify='center')
#        self.intervals.insert('1.0', 'Intervals:\n')
        self.intervals.configure(state='disabled')
#        self.intervals = Label(self, anchor='center',
#                                   justify='center',
#                                   font=CONFIG.get('Timer', 'font_intervals'),
#                                   style='timer.TLabel')
        self.b_interv = Button(self, text='Interval', style='timer.TButton',
                                   command=self.add_interval)
        self.b_interv.state(('disabled',))

        self.b_launch = Button(self, image=self.img_play, padding=2,
                                   command=self.launch, style='timer.TButton')
        self.b_stop = Button(self, image=self.img_stop, padding=2,
                                 command=self.stop, style='timer.TButton')

        # --- placement
#        Button(self, text='x', padding=0, width=1,
#                   style='close.timer.TButton',
#                   command=self.quit).place(x=3, y=5, anchor='w', bordermode="outside")
        self.display.grid(row=0, columnspan=2, sticky='ew', padx=8, pady=(4,0))
        Label(self, text='Intervals:',
                  style='timer.TLabel').grid(row=1, columnspan=2, sticky='w', padx=4)
        self.intervals.grid(row=2, columnspan=2, sticky='eswn')
        self.b_interv.grid(row=3, columnspan=2, sticky='ew')
        self.b_launch.grid(row=4, column=0, sticky='ew')
        self.b_stop.grid(row=4, column=1, sticky='ew')

        self._corner = Sizegrip(self, style="timer.TSizegrip")
        self._corner.place(relx=1, rely=1, anchor='se')

        geometry = CONFIG.get('Timer', 'geometry')
        self.update_idletasks()
        if geometry:
            self.geometry(geometry)
            self.deiconify()

        # --- bindings
        self.intervals.bind("<1>", lambda event: self.intervals.focus_set())
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.display.bind('<ButtonPress-1>', self._start_move)
        self.display.bind('<ButtonRelease-1>', self._stop_move)
        self.display.bind('<B1-Motion>', self._move)
        self.bind('<Configure>', self._on_configure)
        self.display.bind('<Unmap>', self._on_unmap)
        self.display.bind('<Map>', self._on_map)
        self.b_stop.bind('<Enter>', self._on_enter)
        self.b_stop.bind('<Leave>', self._on_leave)

    def _on_enter(self, event=None):
        self._corner.state(('active',))

    def _on_leave(self, event=None):
        self._corner.state(('!active',))

    def _on_map(self, event=None):
        ''' make widget sticky '''
        try:
            for w in self.ewmh.getClientList():
                if w.get_wm_name() == 'scheduler.timer':
                    self.ewmh.setWmState(w, 1, '_NET_WM_STATE_STICKY')
            pos = self._position.get()
            if pos == 'above':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.timer':
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
            elif pos == 'below':
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.timer':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
                        self.ewmh.setWmState(w, 1, '_NET_WM_STATE_BELOW')
            else:
                for w in self.ewmh.getClientList():
                    if w.get_wm_name() == 'scheduler.timer':
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_BELOW')
                        self.ewmh.setWmState(w, 0, '_NET_WM_STATE_ABOVE')
            self.ewmh.display.flush()
            self.variable.set(True)
            save_config()
        except TypeError:
            pass

    def _change_pos(self):
        self.withdraw()
        if self._position.get() == 'above':
            self.overrideredirect(True)
        else:
            self.overrideredirect(False)
        self.deiconify()

    def _on_unmap(self, event):
        CONFIG.set('Timer', 'geometry', '')
        self.variable.set(False)
        save_config()

    def _on_configure(self, event):
        CONFIG.set('Timer', 'geometry', self.geometry())
        self.variable.set(True)
        save_config()

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

    def _run(self):
        if self._on:
            self._time[2] += 1
            if self._time[2] == 60:
                self._time[2] = 0
                self._time[1] += 1
                if self._time[1] == 60:
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
#        text = self.intervals.cget('text')
#        self.intervals.configure(text='\n'.join((text, tps)).strip())

    def stop(self):
        self._on = False
        self.b_interv.state(('disabled',))
        self.b_launch.configure(image=self.img_play)
        self._time = [0, 0, 0]
#        self.intervals.configure(text='')
        self.intervals.configure(state='normal')
        self.intervals.delete('1.0', 'end')
        self.intervals.configure(state='disabled')
        self.display.configure(text='%i:%.2i:%.2i' % tuple(self._time))

#    def quit(self):
#        self.after_cancel(self._after_id)
#        self.destroy()
