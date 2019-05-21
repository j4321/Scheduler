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


Settings
"""
import tkinter as tk
from tkinter import ttk

from PIL.ImageTk import PhotoImage

from schedulerlib.constants import save_config, CONFIG, LANGUAGES, REV_LANGUAGES, \
    TOOLKITS, IM_ADD, IM_DEL, only_nb
from schedulerlib.messagebox import showerror, showinfo, askyesno
from schedulerlib.ttkwidgets import AutoScrollbar
from .font import FontFrame
from .color import ColorFrame
from .sound import SoundFrame
from .opacity import OpacityFrame
from .pomodoro_params import PomodoroParams


class Settings(tk.Toplevel):
    def __init__(self, master=None):
        tk.Toplevel.__init__(self, master, class_='Scheduler')
        self.title(_('Settings'))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.minsize(574, 565)

        self._only_nb = self.register(only_nb)

        self._im_plus = PhotoImage(master=self, file=IM_ADD)
        self._im_moins = PhotoImage(master=self, file=IM_DEL)

        frame = ttk.Frame(self, style='border.TFrame', relief='sunken',
                          border=1)
        self.listbox = tk.Listbox(frame, relief='flat', justify='right',
                                  selectmode='browse', highlightthickness=0,
                                  activestyle='none')
        self.listbox.pack(fill='both', expand=True)
        frame.grid(row=0, column=0, sticky='ns', padx=4, pady=4)

        # --- tabs
        cats = ['General', 'Reminders', 'Calendar', 'Events', 'Pomodoro', 'Tasks', 'Timer']
        self.frames = {}
        self.frames[_('General')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Reminders')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Events')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Tasks')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Timer')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Calendar')] = ttk.Notebook(self)
        self.frames[_('Pomodoro')] = PomodoroParams(self)

        w = 0
        for cat in cats:
            c = _(cat) + ' '
            self.listbox.insert('end', c)
            w = max(len(c), w)
            self.frames[_(cat)].grid(row=0, column=1, sticky='ewns', padx=4, pady=4)
            self.frames[_(cat)].grid_remove()
            self.__getattribute__('_init_{}'.format(cat.lower()))()
        self.listbox.configure(width=w)

        self._current_frame = self.frames[_('General')]
        self._current_frame.grid()
        self.listbox.bind('<<ListboxSelect>>', self._on_listbox_select)
        self.listbox.selection_set(0)

        # --- buttons
        frame_btns = ttk.Frame(self)
        ttk.Button(frame_btns, text=_('Ok'), command=self.ok).pack(side='left', padx=4, pady=10)
        ttk.Button(frame_btns, text=_('Cancel'), command=self.destroy).pack(side='left', padx=4, pady=10)
        frame_btns.grid(row=1, columnspan=2)

    def _init_general(self):
        self.frames[_('General')].columnconfigure(0, weight=1)
        # --- variables
        self.gui = tk.StringVar(self, CONFIG.get("General", "trayicon").capitalize())
        self.lang = tk.StringVar(self, LANGUAGES[CONFIG.get("General", "language")])

        # --- Langue
        lang_frame = ttk.Frame(self.frames[_('General')])

        ttk.Label(lang_frame, text=_("Language")).pack(side="left")
        languages = list(REV_LANGUAGES)
        self.cb_lang = ttk.Combobox(lang_frame, textvariable=self.lang,
                                    state='readonly', style='menu.TCombobox',
                                    exportselection=False,
                                    width=len(max(languages, key=len)) + 1,
                                    values=languages)
        self.cb_lang.pack(side="left", padx=4)
        self.cb_lang.bind('<<ComboboxSelected>>', self.change_langue)
        # --- gui toolkit
        frame_gui = ttk.Frame(self.frames[_('General')])
        ttk.Label(frame_gui,
                  text=_("GUI Toolkit for the system tray icon")).pack(side="left")
        self.cb_gui = ttk.Combobox(frame_gui, textvariable=self.gui,
                                   state='readonly', style='menu.TCombobox',
                                   exportselection=False, width=4,
                                   values=[t.capitalize() for (t, b) in TOOLKITS.items() if b])
        self.cb_gui.pack(side="left", padx=4)
        self.cb_gui.bind('<<ComboboxSelected>>', self.change_gui)
        # --- Update checks
        # self.confirm_update = ttk.Checkbutton(self.frames[_('General')],
                                              # text=_("Check for updates on start-up"))
        # if CONFIG.getboolean('General', 'check_update', fallback=True):
            # self.confirm_update.state(('selected', '!alternate'))
        # else:
            # self.confirm_update.state(('!selected', '!alternate'))

        # --- eyes
        frame_eyes = ttk.Frame(self.frames[_('General')])
        ttk.Label(frame_eyes, text=_("Eyes' rest"),
                  style='title.TLabel').grid(sticky='w', padx=4, pady=4)
        ttk.Label(frame_eyes,
                  text=_("Interval between two eyes' rest (min)")).grid(row=1, column=0, sticky='w', padx=4, pady=4)
        self.eyes_interval = ttk.Entry(frame_eyes, width=4, justify='center',
                                       validate='key',
                                       validatecommand=(self._only_nb, '%P'))
        self.eyes_interval.insert(0, CONFIG.get("General", "eyes_interval", fallback='20'))
        self.eyes_interval.grid(row=1, column=1, sticky='w', padx=4, pady=4)

        # --- Splash supported
        self.splash_support = ttk.Checkbutton(self.frames[_('General')],
                                              text=_("Check this box if the widgets disappear when you click"))
        if not CONFIG.getboolean('General', 'splash_supported', fallback=True):
            self.splash_support.state(('selected', '!alternate'))
        else:
            self.splash_support.state(('!selected', '!alternate'))

        # --- placement
        ttk.Label(self.frames[_('General')], text=_("Interface"),
                  style='title.TLabel').grid(sticky='w', pady=4)
        lang_frame.grid(pady=4, sticky="ew")
        frame_gui.grid(pady=4, sticky="ew")
        # self.confirm_update.grid(pady=4, sticky='w')
        self.splash_support.grid(pady=4, sticky='w')
        ttk.Separator(self.frames[_('General')], orient='horizontal').grid(sticky='ew', pady=10)
        frame_eyes.grid(pady=4, sticky="ew")

    def _init_pomodoro(self):
        pass  # already done in custom class

    def _init_reminders(self):
        # --- window

        def toggle_window():
            b = 'selected' in self.reminders_window.state()
            state = [b * '!' + 'disabled']
            label.state(state)
            self.reminders_timeout.state(state)
            self.reminders_blink.state(state)
            self.reminders_sound.state(state)

        frame_window = ttk.Frame(self.frames[_('Reminders')])
        frame_window.columnconfigure(0, weight=1)
        self.reminders_window = ttk.Checkbutton(frame_window, text=_('Banner'),
                                                style='title.TCheckbutton',
                                                command=toggle_window)
        self.reminders_window.grid(sticky='w', row=0, columnspan=2, column=0, pady=4)
        self.reminders_window.state(('!alternate',
                                     '!' * (not CONFIG.getboolean('Reminders', 'window')) + 'selected'))
        # --- --- timeout
        frame_timeout = ttk.Frame(frame_window)
        frame_timeout.grid(sticky='w', padx=(16, 4), pady=4)
        label = ttk.Label(frame_timeout, text=_('Timeout (min)'))
        label.pack(side='left')
        self.reminders_timeout = ttk.Entry(frame_timeout, width=5,
                                           justify='center', validate='key',
                                           validatecommand=(self._only_nb, '%P'))
        self.reminders_timeout.insert(0, CONFIG.get('Reminders', 'timeout'))
        self.reminders_timeout.pack(side='left', padx=4)
        # --- --- colors
        frame_color = ttk.Frame(frame_window)
        frame_color.grid(sticky='w', padx=(16, 4), pady=4)
        self.reminders_window_bg = ColorFrame(frame_color,
                                              CONFIG.get('Reminders', 'window_bg'),
                                              _('Background'))
        self.reminders_window_bg.pack(side='left', padx=(0, 4))
        self.reminders_window_fg = ColorFrame(frame_color,
                                              CONFIG.get('Reminders', 'window_fg'),
                                              _('Foreground'))
        self.reminders_window_fg.pack(side='left', padx=(4, 0))
        # --- --- opacity
        self.reminders_opacity = OpacityFrame(frame_window,
                                              CONFIG.getfloat('Reminders',
                                                              'window_alpha',
                                                              fallback=0.75),
                                              style='TLabel')
        self.reminders_opacity.grid(sticky='w', padx=(16, 4), pady=4)

        ttk.Separator(frame_window, orient='horizontal').grid(sticky='ew',
                                                              padx=(16, 10),
                                                              pady=10)

        # --- --- blink
        frame_blink = ttk.Frame(frame_window)
        frame_blink.grid(sticky='w', padx=(16, 4), pady=4)

        def toggle_blink():
            b = 'selected' in self.reminders_blink.state()
            state = [b * '!' + 'disabled']
            self.reminders_window_bg_alt.state(state)
            self.reminders_window_fg_alt.state(state)

        self.reminders_blink = ttk.Checkbutton(frame_blink, text=_('Blink'),
                                               command=toggle_blink)
        self.reminders_blink.pack(anchor='nw')
        self.reminders_blink.state(('!alternate',
                                    '!' * (not CONFIG.getboolean('Reminders', 'blink')) + 'selected'))
        self.reminders_window_bg_alt = ColorFrame(frame_blink,
                                                  CONFIG.get('Reminders', 'window_bg_alternate'),
                                                  _('Alternate Background'))
        self.reminders_window_bg_alt.pack(side='left', padx=(16, 4))
        self.reminders_window_fg_alt = ColorFrame(frame_blink,
                                                  CONFIG.get('Reminders', 'window_fg_alternate'),
                                                  _('Alternate Foreground'))
        self.reminders_window_fg_alt.pack(side='left', padx=10)
        toggle_blink()

        ttk.Separator(frame_window, orient='horizontal').grid(sticky='ew',
                                                              padx=(16, 10),
                                                              pady=10)
        # --- --- alarm

        self.reminders_sound = SoundFrame(frame_window, CONFIG.get('Reminders', 'alarm'),
                                          CONFIG.get('Reminders', 'mute'), _('Alarm'))
        self.reminders_sound.grid(sticky='ew', padx=(16, 10), pady=4)

        # --- notif
        frame_notif = ttk.Frame(self.frames[_('Reminders')])
        self.reminders_notif = ttk.Checkbutton(frame_notif, text=_('Notification'),
                                               style='title.TCheckbutton')
        self.reminders_notif.grid(sticky='w', pady=4)
        self.reminders_notif.state(('!alternate',
                                    '!' * (not CONFIG.getboolean('Reminders', 'notification')) + 'selected'))

        # --- placement
        frame_window.pack(anchor='nw', fill='x')
        ttk.Separator(self.frames[_('Reminders')], orient='horizontal').pack(fill='x', pady=10)
        frame_notif.pack(anchor='nw')

    def _init_calendar(self):
        # --- general config
        general = ttk.Frame(self.frames[_('Calendar')], padding=4)
        general.columnconfigure(1, weight=1)
        self.frames[_('Calendar')].add(general, text=_('General'))
        # --- --- opacity
        self.cal_opacity = OpacityFrame(general, CONFIG.getfloat('Calendar', 'alpha', fallback=0.85))
        self.cal_opacity.grid(row=0, columnspan=2, sticky='w', padx=4)

        ttk.Separator(general, orient='horizontal').grid(row=1, columnspan=2,
                                                         pady=10, sticky='ew')
        # --- --- font
        ttk.Label(general, text=_('Font'),
                  style='title.TLabel').grid(row=2, sticky='nw', padx=4, pady=4)
        self.cal_font = FontFrame(general, CONFIG.get('Calendar', 'font'))
        self.cal_font.grid(row=2, column=1, sticky='w', padx=4, pady=4)

        # --- Colors
        frame_color = ttk.Frame(self.frames[_('Calendar')], padding=4)
        frame_color.columnconfigure(3, weight=1)
        self.frames[_('Calendar')].add(frame_color, text=_('Colors'))
        self.cal_colors = {}

        ttk.Label(frame_color, style='subtitle.TLabel',
                  text=_('General')).grid(row=0, column=0, sticky='w')
        self.cal_bg = ColorFrame(frame_color,
                                 CONFIG.get('Calendar', 'background'),
                                 _('Background'))
        self.cal_fg = ColorFrame(frame_color,
                                 CONFIG.get('Calendar', 'foreground'),
                                 _('Foreground'))
        self.cal_bd = ColorFrame(frame_color,
                                 CONFIG.get('Calendar', 'bordercolor'),
                                 _('Border'))
        self.cal_bg.grid(row=0, column=1, sticky='e', padx=8, pady=4)
        self.cal_fg.grid(row=0, column=2, sticky='e', padx=8, pady=4)
        self.cal_bd.grid(row=1, column=1, sticky='e', padx=8, pady=4)

        cal_colors = {'normal': _('Normal day'),
                      'weekend': _('Weekend'),
                      'othermonth': _('Other month day'),
                      'othermonthwe': _('Other month weekend'),
                      'select': _('Selected day'),
                      'headers': _('Headers'),
                      'tooltip': _('Tooltip')}

        for i, (name, label) in enumerate(cal_colors.items()):
            bg = ColorFrame(frame_color,
                            CONFIG.get('Calendar', name + 'background'),
                            _('Background'))
            fg = ColorFrame(frame_color,
                            CONFIG.get('Calendar', name + 'foreground'),
                            _('Foreground'))
            self.cal_colors[name + 'background'] = bg
            self.cal_colors[name + 'foreground'] = fg

            ttk.Separator(frame_color, orient='horizontal').grid(row=2 + 2 * i,
                                                                 columnspan=4,
                                                                 pady=10,
                                                                 sticky='ew')
            ttk.Label(frame_color, style='subtitle.TLabel', wraplength=110,
                      text=label).grid(row=3 + 2 * i, column=0, sticky='w')
            bg.grid(row=3 + 2 * i, column=1, sticky='e', padx=8, pady=4)
            fg.grid(row=3 + 2 * i, column=2, sticky='e', padx=8, pady=4)

        # --- Categories
        categories = ttk.Frame(self.frames[_('Calendar')], padding=4)
        categories.columnconfigure(0, weight=1)
        categories.rowconfigure(0, weight=1)
        self.frames[_('Calendar')].add(categories, text=_('Event categories'))

        can = tk.Canvas(categories, bg=self['bg'],
                        highlightthickness=0, width=1,
                        relief='flat')
        scroll = AutoScrollbar(categories, orient='vertical', command=can.yview)
        can.configure(yscrollcommand=scroll.set)
        can.grid(row=0, column=0, sticky='ewns')
        scroll.grid(row=0, column=1, sticky='ns')

        ttk.Button(categories, image=self._im_plus,
                   command=self.add_cat).grid(row=1, column=0, sticky='w', pady=4)

        self.cat_frame = ttk.Frame(can)
        can.create_window(0, 0, anchor='nw', window=self.cat_frame)

        self.cats = {}
        for i, cat in enumerate(CONFIG.options("Categories")):
            l = ttk.Label(self.cat_frame, text=cat, style='subtitle.TLabel')
            col = CONFIG.get('Categories', cat).split(', ')
            bg = ColorFrame(self.cat_frame, col[1].strip(), _('Background'))
            fg = ColorFrame(self.cat_frame, col[0].strip(), _('Foreground'))
            b = ttk.Button(self.cat_frame, image=self._im_moins, padding=2,
                           command=lambda c=cat: self.del_cat(c))
            self.cats[cat] = [l, bg, fg, b]
            l.grid(row=i, column=0, sticky='e', padx=4, pady=4)
            bg.grid(row=i, column=1, sticky='e', padx=4, pady=4)
            fg.grid(row=i, column=2, sticky='e', padx=4, pady=4)
            b.grid(row=i, column=3, sticky='e', padx=4, pady=4)
        self.update_idletasks()
        can.configure(width=self.cat_frame.winfo_reqwidth())
        can.configure(scrollregion=can.bbox('all'))
        can.bind('<4>', lambda e: self._scroll(e, -1))
        can.bind('<5>', lambda e: self._scroll(e, 1))
        self.cat_frame.bind('<Configure>', lambda e: can.configure(scrollregion=can.bbox('all')))

    def _scroll(self, event, delta):
        if event.widget.yview() != (0, 1):
            event.widget.yview_scroll(delta, 'units')

    def _init_events(self):
        self.frames[_('Events')].columnconfigure(0, weight=1)
        # --- Fonts
        frame_font = ttk.Frame(self.frames[_('Events')])
        frame_font.columnconfigure(2, weight=1)
        ttk.Label(frame_font, text=_('Font'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w', padx=4, pady=4)
        # --- --- title
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Title')).grid(row=1, column=0, sticky='ne', padx=4, pady=8)
        self.events_font_title = FontFrame(frame_font,
                                           CONFIG.get('Events', 'font_title'),
                                           True)
        self.events_font_title.grid(row=1, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=2, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- day
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Day')).grid(row=3, column=0, sticky='ne', padx=4, pady=8)
        self.events_font_day = FontFrame(frame_font,
                                         CONFIG.get('Events', 'font_day'), True)
        self.events_font_day.grid(row=3, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=4, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- text
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Text')).grid(row=5, column=0, sticky='ne', padx=4, pady=8)
        self.events_font = FontFrame(frame_font,
                                     CONFIG.get('Events', 'font'))
        self.events_font.grid(row=5, column=1, padx=4, pady=4)

        # --- opacity
        self.events_opacity = OpacityFrame(self.frames[_('Events')], CONFIG.getfloat("Events", "alpha", fallback=0.85))

        # --- colors
        frame_color = ttk.Frame(self.frames[_('Events')])
        ttk.Label(frame_color, text=_('Colors'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w',
                                             padx=8, pady=4)
        self.events_bg = ColorFrame(frame_color,
                                    CONFIG.get('Events', 'background'),
                                    _('Background'))
        self.events_bg.grid(row=0, column=1, sticky='e', padx=8, pady=4)
        self.events_fg = ColorFrame(frame_color,
                                    CONFIG.get('Events', 'foreground'),
                                    _('Foreground'))
        self.events_fg.grid(row=0, column=2, sticky='e', padx=8, pady=4)

        # --- placement
        frame_font.grid(sticky='ew')
        ttk.Separator(self.frames[_('Events')], orient='horizontal').grid(sticky='ew', pady=8)
        self.events_opacity.grid(sticky='w', padx=4)
        ttk.Separator(self.frames[_('Events')], orient='horizontal').grid(sticky='ew', pady=8)
        frame_color.grid(sticky='w')

    def _init_tasks(self):
        self.frames[_('Tasks')].columnconfigure(0, weight=1)
        self.tasks_hide_comp = tk.BooleanVar(self, CONFIG.getboolean('Tasks', 'hide_completed'))
        # --- Fonts
        frame_font = ttk.Frame(self.frames[_('Tasks')])
        frame_font.columnconfigure(2, weight=1)
        ttk.Label(frame_font, text=_('Font'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w', padx=4, pady=4)
        # --- --- title
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Title')).grid(row=1, column=0, sticky='nw', padx=4, pady=8)
        self.tasks_font_title = FontFrame(frame_font,
                                          CONFIG.get('Tasks', 'font_title'),
                                          True)
        self.tasks_font_title.grid(row=1, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=2, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- text
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Text')).grid(row=5, column=0, sticky='nw', padx=4, pady=8)
        self.tasks_font = FontFrame(frame_font,
                                    CONFIG.get('Tasks', 'font'))
        self.tasks_font.grid(row=5, column=1, padx=4, pady=4)

        # --- opacity
        self.tasks_opacity = OpacityFrame(self.frames[_('Tasks')], CONFIG.getfloat("Tasks", "alpha", fallback=0.85))

        # --- colors
        frame_color = ttk.Frame(self.frames[_('Tasks')])
        ttk.Label(frame_color, text=_('Colors'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w',
                                             padx=8, pady=4)
        self.tasks_bg = ColorFrame(frame_color,
                                   CONFIG.get('Tasks', 'background'),
                                   _('Background'))
        self.tasks_bg.grid(row=0, column=1, sticky='e', padx=8, pady=4)
        self.tasks_fg = ColorFrame(frame_color,
                                   CONFIG.get('Tasks', 'foreground'),
                                   _('Foreground'))
        self.tasks_fg.grid(row=0, column=2, sticky='e', padx=8, pady=4)

        # --- placement
        frame_font.grid(sticky='ew')
        ttk.Separator(self.frames[_('Tasks')], orient='horizontal').grid(sticky='ew', pady=8)
        self.tasks_opacity.grid(sticky='w', padx=4)
        ttk.Separator(self.frames[_('Tasks')], orient='horizontal').grid(sticky='ew', pady=8)
        frame_color.grid(sticky='w')
        ttk.Separator(self.frames[_('Tasks')], orient='horizontal').grid(sticky='ew', pady=8)
        ttk.Checkbutton(self.frames[_('Tasks')], text=_('Hide completed tasks'),
                        variable=self.tasks_hide_comp).grid(sticky='w', padx=4, pady=4)

    def _init_timer(self):
        self.frames[_('Timer')].columnconfigure(0, weight=1)
        # --- Fonts
        frame_font = ttk.Frame(self.frames[_('Timer')])
        frame_font.columnconfigure(2, weight=1)
        ttk.Label(frame_font, text=_('Font'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w', padx=4, pady=4)
        # --- --- time
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Time')).grid(row=1, column=0, sticky='nw', padx=4, pady=8)
        self.timer_font_time = FontFrame(frame_font,
                                         CONFIG.get('Timer', 'font_time'),
                                         sample_text="02:17")
        self.timer_font_time.grid(row=1, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=2, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- intervals
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Intervals')).grid(row=5, column=0, sticky='nw', padx=4, pady=8)
        self.timer_font_intervals = FontFrame(frame_font,
                                              CONFIG.get('Timer', 'font_intervals'), sample_text="02:17")
        self.timer_font_intervals.grid(row=5, column=1, padx=4, pady=4)

        # --- opacity
        self.timer_opacity = OpacityFrame(self.frames[_('Timer')], CONFIG.getfloat("Timer", "alpha", fallback=0.85))

        # --- colors
        frame_color = ttk.Frame(self.frames[_('Timer')])
        ttk.Label(frame_color, text=_('Colors'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w',
                                             padx=8, pady=4)
        self.timer_bg = ColorFrame(frame_color,
                                   CONFIG.get('Timer', 'background'),
                                   _('Background'))
        self.timer_bg.grid(row=0, column=1, sticky='e', padx=8, pady=4)
        self.timer_fg = ColorFrame(frame_color,
                                   CONFIG.get('Timer', 'foreground'),
                                   _('Foreground'))
        self.timer_fg.grid(row=0, column=2, sticky='e', padx=8, pady=4)

        # --- placement
        frame_font.grid(sticky='ew')
        ttk.Separator(self.frames[_('Timer')], orient='horizontal').grid(sticky='ew', pady=8)
        self.timer_opacity.grid(sticky='w', padx=4)
        ttk.Separator(self.frames[_('Timer')], orient='horizontal').grid(sticky='ew', pady=8)
        frame_color.grid(sticky='w')

    def _on_listbox_select(self, event):
        try:
            index = self.listbox.curselection()[0]
        except IndexError:
            return
        self._current_frame.grid_remove()
        self._current_frame = self.frames[self.listbox.get(index).strip()]
        self._current_frame.grid()

    def change_langue(self, event=None):
        self.cb_lang.selection_clear()
        showinfo(_("Information"),
                 _("The language setting will take effect after restarting the application."),
                 parent=self)

    def change_gui(self, event=None):
        self.cb_gui.selection_clear()
        showinfo(_("Information"),
                 _("The GUI Toolkit setting will take effect after restarting the application"),
                 parent=self)

    def del_cat(self, cat):
        rep = askyesno(_("Confirmation"),
                       _("Are you sure you want to delete the category {category}? This action cannot be undone.").format(category=cat))
        if rep:
            CONFIG.remove_option("Categories", cat)
            for w in self.cats[cat]:
                w.destroy()
            del self.cats[cat]
            save_config()

    def add_cat(self):

        def ok(event):
            cat = name.get().strip().lower()
            if cat in self.cats:
                showerror(_("Error"),
                          _("The category {category} already exists.").format(category=cat),
                          parent=self)
            elif cat:
                i = self.cat_frame.grid_size()[1] + 1
                col = 'white', '#186CBE'
                l = ttk.Label(self.cat_frame, text=cat, style='subtitle.TLabel')
                bg = ColorFrame(self.cat_frame, col[1].strip(), _('Background'))
                fg = ColorFrame(self.cat_frame, col[0].strip(), _('Foreground'))
                b = ttk.Button(self.cat_frame, image=self._im_moins, padding=2,
                               command=lambda c=cat: self.del_cat(c))
                self.cats[cat] = [l, bg, fg, b]
                l.grid(row=i, column=0, sticky='e', padx=4, pady=4)
                bg.grid(row=i, column=1, sticky='e', padx=4, pady=4)
                fg.grid(row=i, column=2, sticky='e', padx=4, pady=4)
                b.grid(row=i, column=3, sticky='e', padx=4, pady=4)
            top.destroy()

        top = tk.Toplevel(self)
        top.resizable(True, False)
        top.transient(self)
        top.title(_('New category'))
        top.grab_set()
        top.geometry('+%i+%i' % self.winfo_pointerxy())

        ttk.Label(top, text=_('Category')).pack(side='left', padx=(10, 4), pady=10)
        name = ttk.Entry(top, width=10, justify='center')
        name.pack(side='left', padx=(14, 0), pady=10, fill='y', expand=True)
        name.focus_set()
        name.bind('<Escape>', lambda e: top.destroy())
        name.bind('<Return>', ok)

    def ok(self):
        # --- General
        CONFIG.set("General", "language", REV_LANGUAGES[self.lang.get()])
        CONFIG.set("General", "trayicon", self.gui.get().lower())
        # CONFIG.set("General", "check_update", str('selected' in self.confirm_update.state()))
        CONFIG.set('General', 'splash_supported', str(not self.splash_support.instate(('selected',))))

        eyes = self.eyes_interval.get()
        if eyes == '':
            eyes = '20'
        CONFIG.set("General", "eyes_interval", eyes)
        # --- Reminders
        CONFIG.set("Reminders", 'window', str("selected" in self.reminders_window.state()))
        CONFIG.set("Reminders", 'window_bg', self.reminders_window_bg.get_color())
        CONFIG.set("Reminders", 'window_fg', self.reminders_window_fg.get_color())
        CONFIG.set("Reminders", "window_alpha", "%.2f" % (self.reminders_opacity.get_opacity()))
        CONFIG.set("Reminders", 'window_bg_alternate', self.reminders_window_bg_alt.get_color())
        CONFIG.set("Reminders", 'window_fg_alternate', self.reminders_window_fg_alt.get_color())
        CONFIG.set("Reminders", 'blink', str("selected" in self.reminders_blink.state()))
        CONFIG.set("Reminders", 'notification', str("selected" in self.reminders_notif.state()))
        alarm, mute = self.reminders_sound.get()
        CONFIG.set("Reminders", 'alarm', alarm)
        timeout = self.reminders_timeout.get()
        if timeout == '':
            timeout = '5'
        CONFIG.set("Reminders", 'timeout', timeout)
        CONFIG.set("Reminders", 'mute', str(mute))
        # --- Calendar
        CONFIG.set("Calendar", "alpha", "%.2f" % (self.cal_opacity.get_opacity()))

        font = self.cal_font.get_font()
        CONFIG.set("Calendar", "font", "{} {}".format(font['family'].replace(' ', '\ '),
                                                      font['size']))
        CONFIG.set("Calendar", "bordercolor", self.cal_bd.get_color())
        CONFIG.set("Calendar", "background", self.cal_bg.get_color())
        CONFIG.set("Calendar", "foreground", self.cal_fg.get_color())
        for name, widget in self.cal_colors.items():
            CONFIG.set("Calendar", name, widget.get_color())

        for cat, (l, bg, fg, b) in self.cats.items():
            CONFIG.set("Categories", cat, "{}, {}".format(fg.get_color(), bg.get_color()))

        # --- Events
        CONFIG.set("Events", "alpha", "%.2f" % (self.events_opacity.get_opacity()))

        font = self.events_font.get_font()
        CONFIG.set("Events", "font", "{} {}".format(font['family'].replace(' ', '\ '),
                                                    font['size']))
        font_title = self.events_font_title.get_font()
        title = [font_title['family'].replace(' ', '\ '), str(font_title['size']),
                 font_title['weight'], font_title['slant']]
        if font_title['underline']:
            title.append('underline')
        CONFIG.set("Events", "font_title", " ".join(title))

        font_day = self.events_font_day.get_font()
        day = [font_day['family'].replace(' ', '\ '), str(font_day['size']),
               font_day['weight'], font_day['slant']]
        if font_day['underline']:
            day.append('underline')
        CONFIG.set("Events", "font_day", " ".join(day))

        CONFIG.set("Events", "background", self.events_bg.get_color())
        CONFIG.set("Events", "foreground", self.events_fg.get_color())

        # --- Tasks
        CONFIG.set("Tasks", "alpha", "%.2f" % (self.tasks_opacity.get_opacity()))

        font = self.tasks_font.get_font()
        CONFIG.set("Tasks", "font", "{} {}".format(font['family'].replace(' ', '\ '),
                                                   font['size']))
        font_title = self.tasks_font_title.get_font()
        title = [font_title['family'].replace(' ', '\ '), str(font_title['size']),
                 font_title['weight'], font_title['slant']]
        if font_title['underline']:
            title.append('underline')
        CONFIG.set("Tasks", "font_title", " ".join(title))

        CONFIG.set("Tasks", "background", self.tasks_bg.get_color())
        CONFIG.set("Tasks", "foreground", self.tasks_fg.get_color())
        CONFIG.set('Tasks', 'hide_completed', str(self.tasks_hide_comp.get()))

        # --- Timer
        CONFIG.set("Timer", "alpha", "%.2f" % (self.timer_opacity.get_opacity()))

        font_time = self.timer_font_time.get_font()
        CONFIG.set("Timer", "font_time", "{} {}".format(font_time['family'].replace(' ', '\ '),
                                                        font_time['size']))
        font_intervals = self.timer_font_intervals.get_font()
        CONFIG.set("Timer", "font_intervals", "{} {}".format(font_intervals['family'].replace(' ', '\ '),
                                                             font_intervals['size']))

        CONFIG.set("Timer", "background", self.timer_bg.get_color())
        CONFIG.set("Timer", "foreground", self.timer_fg.get_color())

        # --- Pomodoro
        stop_pomodoro = self.frames[_('Pomodoro')].valide()
        if stop_pomodoro:
            self.master.widgets['Pomodoro'].stop(False)
        save_config()
        self.destroy()
