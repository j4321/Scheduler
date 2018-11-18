#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2018 Juliette Monsel <j_4321@protonmail.com>
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


Settings
"""

import tkinter as tk
from tkinter import ttk
from .font import FontFrame
from .color import ColorFrame
from .opacity import OpacityFrame
from .pomodoro_params import PomodoroParams
from schedulerlib.constants import save_config, CONFIG, LANGUAGES, REV_LANGUAGES, \
    TOOLKITS, PLUS
from schedulerlib.messagebox import showerror, showinfo
from schedulerlib.ttkwidgets import AutoScrollbar
from PIL.ImageTk import PhotoImage


class Settings(tk.Toplevel):
    def __init__(self, master=None, **kw):
        tk.Toplevel.__init__(self, master, **kw)
        self.title(_('Settings'))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, style='border.TFrame', relief='sunken',
                          border=1)
        self.listbox = tk.Listbox(frame, relief='flat', justify='right',
                                  selectmode='browse', highlightthickness=0,
                                  width=10, activestyle='none')
        self.listbox.pack(fill='both', expand=True)
        frame.grid(row=0, column=0, sticky='ns', padx=4, pady=4)

        cats = ['General', 'Calendar', 'Events', 'Pomodoro', 'Tasks', 'Timer']
        self.frames = {}
        self.frames[_('General')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Events')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Tasks')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Timer')] = ttk.Frame(self, relief='raised', border=1, padding=10)
        self.frames[_('Calendar')] = ttk.Notebook(self)
        self.frames[_('Pomodoro')] = PomodoroParams(self)

        for cat in cats:
            self.listbox.insert('end', _(cat) + ' ')
            self.frames[_(cat)].grid(row=0, column=1, sticky='ewns', padx=4, pady=4)
            self.frames[_(cat)].grid_remove()

        self._init_general()
        self._init_calendar()
        self._init_events()
        self._init_tasks()
        self._init_timer()

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
        # --- variables
        self.gui = tk.StringVar(self, CONFIG.get("General", "trayicon").capitalize())
        self.lang = tk.StringVar(self, LANGUAGES[CONFIG.get("General", "language")])

        # --- Langue
        lang_frame = ttk.Frame(self.frames[_('General')])
        lang_frame.grid(pady=4, sticky="ew")
        ttk.Label(lang_frame, text=_("Language:")).pack(side="left")

        menu_lang = tk.Menu(lang_frame)
        for lang in REV_LANGUAGES:
            menu_lang.add_radiobutton(label=lang, variable=self.lang,
                                      value=lang, command=self.change_langue)
        ttk.Menubutton(lang_frame, textvariable=self.lang,
                       menu=menu_lang).pack(side="left", padx=4)
        # --- gui toolkit
        frame_gui = ttk.Frame(self.frames[_('General')])
        frame_gui.grid(pady=4, sticky="ew")
        ttk.Label(frame_gui,
                  text=_("GUI Toolkit for the system tray icon:")).pack(side="left")
        menu_gui = tk.Menu(frame_gui)
        ttk.Menubutton(frame_gui, menu=menu_gui, width=9,
                       textvariable=self.gui).pack(side="left", padx=4)

        for toolkit, b in TOOLKITS.items():
            if b:
                menu_gui.add_radiobutton(label=toolkit.capitalize(),
                                         value=toolkit.capitalize(),
                                         variable=self.gui,
                                         command=self.change_gui)
        # --- Update checks
        self.confirm_update = ttk.Checkbutton(self.frames[_('General')],
                                              text=_("Check for updates on start-up"))
        self.confirm_update.grid(pady=4, sticky='w')
        if CONFIG.getboolean('General', 'check_update', fallback=True):
            self.confirm_update.state(('selected', '!alternate'))
        else:
            self.confirm_update.state(('!selected', '!alternate'))

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
                  text=_('General')).grid(row=0, column=0, sticky='e')
        self.cal_bg = ColorFrame(frame_color,
                                 CONFIG.get('Calendar', 'background'),
                                 _('Background'))
        self.cal_fg = ColorFrame(frame_color,
                                 CONFIG.get('Calendar', 'foreground'),
                                 _('Foreground'))
        self.cal_bd = ColorFrame(frame_color,
                                 CONFIG.get('Calendar', 'bordercolor'),
                                 _('Bordercolor'))
        self.cal_bg.grid(row=0, column=1, sticky='e')
        self.cal_fg.grid(row=0, column=2, sticky='e')
        self.cal_bd.grid(row=1, column=1, sticky='e')

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
            ttk.Label(frame_color, style='subtitle.TLabel',
                      text=label).grid(row=3 + 2 * i, column=0, sticky='e', padx=(0, 4))
            bg.grid(row=3 + 2 * i, column=1, sticky='e')
            fg.grid(row=3 + 2 * i, column=2, sticky='e')

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

        self._im_plus = PhotoImage(master=self, file=PLUS)
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
            self.cats[cat] = [l, bg, fg]
            l.grid(row=i, column=0, sticky='e', padx=4, pady=4)
            bg.grid(row=i, column=1, sticky='e', padx=4, pady=4)
            fg.grid(row=i, column=2, sticky='e', padx=4, pady=4)
        self.update_idletasks()
        can.configure(width=self.cat_frame.winfo_reqwidth())
        can.configure(scrollregion=can.bbox('all'))
        self.cat_frame.bind('<Configure>', lambda e: can.configure(scrollregion=can.bbox('all')))

    def _init_events(self):
        self.frames[_('Events')].columnconfigure(0, weight=1)
        # --- Fonts
        frame_font = ttk.Frame(self.frames[_('Events')])
        frame_font.columnconfigure(2, weight=1)
        ttk.Label(frame_font, text=_('Font'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w', padx=4, pady=4)
        # --- --- title
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Title')).grid(row=1, column=0, sticky='e', padx=4, pady=4)
        self.events_font_title = FontFrame(frame_font,
                                           CONFIG.get('Events', 'font_title'),
                                           True)
        self.events_font_title.grid(row=1, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=2, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- day
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Day')).grid(row=3, column=0, sticky='e', padx=4, pady=4)
        self.events_font_day = FontFrame(frame_font,
                                         CONFIG.get('Events', 'font_day'), True)
        self.events_font_day.grid(row=3, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=4, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- text
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Text')).grid(row=5, column=0, sticky='e', padx=4, pady=4)
        self.events_font = FontFrame(frame_font,
                                     CONFIG.get('Events', 'font'))
        self.events_font.grid(row=5, column=1, padx=4, pady=4)

        # --- opacity
        self.events_opacity = OpacityFrame(self.frames[_('Events')], CONFIG.getfloat("Events", "alpha", fallback=0.85))

        # --- colors
        frame_color = ttk.Frame(self.frames[_('Events')])
        ttk.Label(frame_color, text=_('Colors'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w',
                                             padx=4, pady=4)
        self.events_bg = ColorFrame(frame_color,
                                    CONFIG.get('Events', 'background'),
                                    _('Background'))
        self.events_bg.grid(row=0, column=1, sticky='e')
        self.events_fg = ColorFrame(frame_color,
                                    CONFIG.get('Events', 'foreground'),
                                    _('Foreground'))
        self.events_fg.grid(row=1, column=1, sticky='e')

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
                  text=_('Title')).grid(row=1, column=0, sticky='w', padx=4, pady=4)
        self.tasks_font_title = FontFrame(frame_font,
                                          CONFIG.get('Tasks', 'font_title'),
                                          True)
        self.tasks_font_title.grid(row=1, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=2, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- text
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Text')).grid(row=5, column=0, sticky='w', padx=4, pady=4)
        self.tasks_font = FontFrame(frame_font,
                                    CONFIG.get('Tasks', 'font'))
        self.tasks_font.grid(row=5, column=1, padx=4, pady=4)

        # --- opacity
        self.tasks_opacity = OpacityFrame(self.frames[_('Tasks')], CONFIG.getfloat("Tasks", "alpha", fallback=0.85))

        # --- colors
        frame_color = ttk.Frame(self.frames[_('Tasks')])
        ttk.Label(frame_color, text=_('Colors'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w',
                                             padx=4, pady=4)
        self.tasks_bg = ColorFrame(frame_color,
                                   CONFIG.get('Tasks', 'background'),
                                   _('Background'))
        self.tasks_bg.grid(row=0, column=1, sticky='e')
        self.tasks_fg = ColorFrame(frame_color,
                                   CONFIG.get('Tasks', 'foreground'),
                                   _('Foreground'))
        self.tasks_fg.grid(row=1, column=1, sticky='e')

        # --- placement
        ttk.Checkbutton(self.frames[_('Tasks')], text=_('Hide completed tasks'),
                        variable=self.tasks_hide_comp).grid(sticky='w', padx=4, pady=4)
        ttk.Separator(self.frames[_('Tasks')], orient='horizontal').grid(sticky='ew', pady=8)
        frame_font.grid(sticky='w')
        ttk.Separator(self.frames[_('Tasks')], orient='horizontal').grid(sticky='ew', pady=8)
        self.tasks_opacity.grid(sticky='w', padx=4)
        ttk.Separator(self.frames[_('Tasks')], orient='horizontal').grid(sticky='ew', pady=8)
        frame_color.grid(sticky='w')

    def _init_timer(self):
        self.frames[_('Timer')].columnconfigure(0, weight=1)
        # --- Fonts
        frame_font = ttk.Frame(self.frames[_('Timer')])
        frame_font.columnconfigure(2, weight=1)
        ttk.Label(frame_font, text=_('Font'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w', padx=4, pady=4)
        # --- --- time
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Time')).grid(row=1, column=0, sticky='w', padx=4, pady=4)
        self.timer_font_time = FontFrame(frame_font,
                                         CONFIG.get('Timer', 'font_time'),
                                         sample_text="02:17")
        self.timer_font_time.grid(row=1, column=1, padx=4, pady=4)
        ttk.Separator(frame_font,
                      orient='horizontal').grid(row=2, columnspan=3, padx=10, pady=4, sticky='ew')
        # --- --- intervals
        ttk.Label(frame_font, style='subtitle.TLabel',
                  text=_('Intervals')).grid(row=5, column=0, sticky='w', padx=4, pady=4)
        self.timer_font_intervals = FontFrame(frame_font,
                                              CONFIG.get('Timer', 'font_intervals'), sample_text="02:17")
        self.timer_font_intervals.grid(row=5, column=1, padx=4, pady=4)

        # --- opacity
        self.timer_opacity = OpacityFrame(self.frames[_('Timer')], CONFIG.getfloat("Timer", "alpha", fallback=0.85))

        # --- colors
        frame_color = ttk.Frame(self.frames[_('Timer')])
        ttk.Label(frame_color, text=_('Colors'),
                  style='title.TLabel').grid(row=0, column=0, sticky='w',
                                             padx=4, pady=4)
        self.timer_bg = ColorFrame(frame_color,
                                   CONFIG.get('Timer', 'background'),
                                   _('Background'))
        self.timer_bg.grid(row=0, column=1, sticky='e')
        self.timer_fg = ColorFrame(frame_color,
                                   CONFIG.get('Timer', 'foreground'),
                                   _('Foreground'))
        self.timer_fg.grid(row=1, column=1, sticky='e')

        # --- placement
        frame_font.grid(sticky='w')
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

    def change_langue(self):
        showinfo(_("Information"),
                 _("The language setting will take effect after restarting the application."),
                 parent=self)

    def change_gui(self):
        showinfo(_("Information"),
                 _("The GUI Toolkit setting will take effect after restarting the application"),
                 parent=self)

    def add_cat(self):

        def ok(event):
            cat = name.get().strip().lower()
            if cat in self.cats:
                showerror(_("Error"),
                          _("The category {category} already exists.").format(category=cat))
            else:
                i = self.cat_frame.grid_size()[1] + 1
                col = 'white', '#186CBE'
                l = ttk.Label(self.cat_frame, text=cat, style='subtitle.TLabel')
                bg = ColorFrame(self.cat_frame, col[1].strip(), _('Background'))
                fg = ColorFrame(self.cat_frame, col[0].strip(), _('Foreground'))
                self.cats[cat] = [l, bg, fg]
                l.grid(row=i, column=0, sticky='e', padx=4, pady=4)
                bg.grid(row=i, column=1, sticky='e', padx=4, pady=4)
                fg.grid(row=i, column=2, sticky='e', padx=4, pady=4)
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
        CONFIG.set("General", "check_update", str('selected' in self.confirm_update.state()))

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

        for cat, (l, bg, fg) in self.cats.items():
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
