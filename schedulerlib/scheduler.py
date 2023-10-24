#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2020 Juliette Monsel <j_4321@protonmail.com>

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


Task manager (main app)
"""
import os
import shutil
import logging
import traceback
import signal
import requests
from subprocess import Popen
from pickle import Pickler, Unpickler
from tkinter import Tk, Menu, StringVar, TclError, BooleanVar, Toplevel
from tkinter import PhotoImage as tkPhotoImage
from tkinter.ttk import Button, Treeview, Style, Label, Combobox, Frame, Entry
from datetime import datetime, timedelta

from babel.dates import get_date_format
from PIL import Image
from PIL.ImageTk import PhotoImage
from dateutil.parser import parse
import icalendar
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.triggers.cron import CronTrigger
from tkcalendar import DateEntry

from schedulerlib.messagebox import showerror, askokcancel, askoptions
from schedulerlib.constants import IMAGES, ICON, ICON_FALLBACK, IM_SCROLL_ALPHA, \
    CONFIG, JOBSTORE, DATA_PATH, BACKUP_PATH, active_color, backup, add_trace, \
    format_time, askopenfilename, asksaveasfilename, OPENFILE_PATH, ICON_NOTIF
from schedulerlib.trayicon import TrayIcon, SubMenu
from schedulerlib.form import Form
from schedulerlib.event import Event
from schedulerlib.widgets import EventWidget, Timer, TaskWidget, Pomodoro, CalendarWidget
from schedulerlib.settings import Settings
from schedulerlib.ttkwidgets import AutoScrollbar
from schedulerlib.about import About
from schedulerlib.eyes import Eyes


class EventScheduler(Tk):
    """Main class."""
    def __init__(self, *files):
        """
        Create the main window containing the task manager.

        files: list of .ics files to load in the calendar
        """
        Tk.__init__(self, className='Scheduler')
        logging.info('Start')
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self._visible = BooleanVar(self, False)
        self.withdraw()

        # --- systray icon
        self.icon = TrayIcon(ICON, fallback_icon_path=ICON_FALLBACK)

        # --- images
        self._images = {name: PhotoImage(name=f'img_{name}', file=IMAGES[name], master=self)
                        for name, path in IMAGES.items()}
        self.iconphoto(True, 'img_icon48')


        # --- menu
        self.menu_widgets = SubMenu(parent=self.icon.menu)
        self.menu_eyes = Eyes(self.icon.menu, self)
        self.icon.menu.add_checkbutton(label=_('Silent mode'), command=self.toggle_silent_mode)
        self.icon.menu.set_item_value(_('Silent mode'), CONFIG.getboolean('General', 'silent_mode'))
        self.icon.menu.add_separator()
        self.icon.menu.add_checkbutton(label=_('Manager'), command=self.display_hide)
        self.icon.menu.add_cascade(label=_('Widgets'), menu=self.menu_widgets)
        self.icon.menu.add_cascade(label=_("Eyes' rest"), menu=self.menu_eyes)
        self.icon.menu.add_command(label=_('Settings'), command=self.settings)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_("Export to .ics"), command=self.export_ical)
        self.icon.menu.add_command(label=_("Load .ics file"), command=self.load_ics_file)
        self.icon.menu.add_command(label=_("Load .ics from url"), command=self.load_ics_url)
        self.icon.menu.add_separator()
        self.icon.menu.add_command(label=_('About'), command=lambda: About(self))
        self.icon.menu.add_command(label=_('Quit'), command=self.exit)
        self.icon.bind_left_click(lambda: self.display_hide(toggle=True))

        add_trace(self._visible, 'write', self._visibility_trace)

        self.menu = Menu(self, tearoff=False)
        self.menu.add_command(label=_('Edit'), command=self._edit_menu)
        self.menu.add_command(label=_('Delete'), command=self._delete_menu)
        self.right_click_iid = None

        self.menu_task = Menu(self.menu, tearoff=False)
        self._task_var = StringVar(self)
        menu_in_progress = Menu(self.menu_task, tearoff=False)
        for i in range(0, 110, 10):
            prog = '{}%'.format(i)
            menu_in_progress.add_radiobutton(label=prog, value=prog,
                                             variable=self._task_var,
                                             command=self._set_progress)
        for state in ['Pending', 'Completed', 'Cancelled']:
            self.menu_task.add_radiobutton(label=_(state), value=state,
                                           variable=self._task_var,
                                           command=self._set_progress)
        self._img_dot = tkPhotoImage(master=self)
        self.menu_task.insert_cascade(1, menu=menu_in_progress,
                                      compound='left',
                                      label=_('In Progress'),
                                      image=self._img_dot)
        self.title('Scheduler')
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.scheduler = BackgroundScheduler(coalesce=False,
                                             misfire_grace_time=86400)
        self.scheduler.add_jobstore('sqlalchemy',
                                    url='sqlite:///%s' % JOBSTORE)
        self.scheduler.add_jobstore('memory', alias='memo')

        # --- style
        self.style = Style(self)
        self.style.theme_use("clam")
        self.style.configure('nav.TButton', background='white')
        self.style.configure('title.TLabel', font='TkdefaultFont 10 bold')
        self.style.configure('title.TCheckbutton', font='TkdefaultFont 10 bold')
        self.style.configure('subtitle.TLabel', font='TkdefaultFont 9 bold')
        self.style.configure('white.TLabel', background='white')
        self.style.configure('border.TFrame', background='white', border=1, relief='sunken')
        self.style.configure("Treeview.Heading", font="TkDefaultFont")
        bgc = self.style.lookup("TButton", "background")
        fgc = self.style.lookup("TButton", "foreground")
        fgd = self.style.lookup("TEntry", "foreground", ("disabled",))
        bga = self.style.lookup("TButton", "background", ("active",))
        self.style.map('TCombobox',
                       fieldbackground=[('readonly', 'white'),
                                        ('readonly', 'focus', 'white')],
                       background=[("disabled", "active", "readonly", bgc),
                                   ("!disabled", "active", "readonly", bga)],
                       foreground=[('readonly', '!disabled', fgc),
                                   ('readonly', '!disabled', 'focus', fgc),
                                   ('!readonly', 'disabled', fgd),
                                   ('readonly', 'disabled', fgd),
                                   ('readonly', 'disabled', 'focus', fgd)],
                       arrowcolor=[("disabled", "gray40")])
        self.style.configure('menu.TCombobox', foreground=fgc, background=bgc,
                             fieldbackground=bgc)
        self.style.map('menu.TCombobox',
                       fieldbackground=[('readonly', bgc),
                                        ('readonly', 'focus', bgc)],
                       background=[("disabled", "active", "readonly", bgc),
                                   ("!disabled", "active", "readonly", bga)],
                       foreground=[('readonly', '!disabled', fgc),
                                   ('readonly', '!disabled', 'focus', fgc),
                                   ('readonly', 'disabled', 'gray40'),
                                   ('readonly', 'disabled', 'focus', 'gray40')],
                       arrowcolor=[("disabled", "gray40")])
        self.style.map('DateEntry', arrowcolor=[("disabled", "gray40")])
        self.style.configure('cal.TFrame', background='#424242')
        self.style.configure('month.TLabel', background='#424242', foreground='white')
        self.style.configure('R.TButton', background='#424242',
                             arrowcolor='white', bordercolor='#424242',
                             lightcolor='#424242', darkcolor='#424242')
        self.style.configure('L.TButton', background='#424242',
                             arrowcolor='white', bordercolor='#424242',
                             lightcolor='#424242', darkcolor='#424242')
        active_bg = self.style.lookup('TEntry', 'selectbackground', ('focus',))
        self.style.map('R.TButton', background=[('active', active_bg)],
                       bordercolor=[('active', active_bg)],
                       darkcolor=[('active', active_bg)],
                       lightcolor=[('active', active_bg)])
        self.style.map('L.TButton', background=[('active', active_bg)],
                       bordercolor=[('active', active_bg)],
                       darkcolor=[('active', active_bg)],
                       lightcolor=[('active', active_bg)])
        self.style.configure('txt.TFrame', background='white')
        self.style.layout('down.TButton',
                          [('down.TButton.downarrow',
                            {'side': 'right', 'sticky': 'ns'})])
        self.style.map('TRadiobutton',
                       indicatorforeground=[('disabled', 'gray40')])
        self.style.map('TCheckbutton',
                       indicatorforeground=[('disabled', 'gray40')],
                       indicatorbackground=[('pressed', '#dcdad5'),
                                            ('!disabled', 'alternate', 'white'),
                                            ('disabled', 'alternate', '#a0a0a0'),
                                            ('disabled', '#dcdad5')])
        self.style.map('down.TButton',
                       arrowcolor=[("disabled", "gray40")])

        self.style.map('TMenubutton',
                       arrowcolor=[('disabled',
                                    self.style.lookup('TMenubutton', 'foreground', ['disabled']))])
        bg = self.style.lookup('TFrame', 'background', default='#ececec')
        self.configure(bg=bg)
        self.option_add('*Scheduler.background', bg)
        self.option_add('*Toplevel.background', bg)
        self.option_add('*Menu.background', bg)
        self.option_add('*Menu.tearOff', False)
        self.option_add('*Text.relief', 'flat')
        self.option_add('*Text.highlightThickness', 0)
        self.option_add('*Text.selectBackground',
                        self.style.lookup('TEntry', 'selectbackground', ('focus',)))
        self.option_add('*Text.inactiveSelectBackground',
                        self.style.lookup('TEntry', 'selectforeground'))
        self.option_add('*Text.selectForeground',
                        self.style.lookup('TEntry', 'selectforeground', ('focus',)))
        self.option_add('*Text.inactiveSelectForeground',
                        self.style.lookup('TEntry', 'selectforeground'))
        # toggle text
        self.style.element_create("toggle", "image", "img_closed",
                                  ("selected", "!disabled", "img_opened"),
                                  ("active", "!selected", "!disabled", "img_closed_sel"),
                                  ("active", "selected", "!disabled", "img_opened_sel"),
                                  border=2, sticky='')
        self.style.map('Toggle', background=[])
        self.style.layout('Toggle',
                          [('Toggle.border',
                            {'children': [('Toggle.padding',
                                           {'children': [('Toggle.toggle',
                                                          {'sticky': 'nswe'})],
                                            'sticky': 'nswe'})],
                             'sticky': 'nswe'})])
        # toggle sound
        self.style.element_create('mute', 'image', 'img_sound',
                                  ('selected', '!disabled', 'img_mute'),
                                  ('selected', 'disabled', 'img_mute_dis'),
                                  ('!selected', 'disabled', 'img_sound_dis'),
                                  border=2, sticky='')
        self.style.layout('Mute',
                          [('Mute.border',
                            {'children': [('Mute.padding',
                                           {'children': [('Mute.mute',
                                                          {'sticky': 'nswe'})],
                                            'sticky': 'nswe'})],
                             'sticky': 'nswe'})])
        self.style.configure('Mute', relief='raised')
        # widget scrollbar
        self._im_trough = {}
        self._im_slider_vert = {}
        self._im_slider_vert_prelight = {}
        self._im_slider_vert_active = {}
        self._slider_alpha = Image.open(IM_SCROLL_ALPHA)
        for widget in ['Events', 'Tasks', 'Timer']:
            bg = CONFIG.get(widget, 'background')
            fg = CONFIG.get(widget, 'foreground')

            widget_bg = self.winfo_rgb(bg)
            widget_fg = tuple(round(c * 255 / 65535) for c in self.winfo_rgb(fg))
            active_bg = active_color(*widget_bg)
            active_bg2 = active_color(*active_color(*widget_bg, 'RGB'))

            slider_vert = Image.new('RGBA', (13, 28), active_bg)
            slider_vert_active = Image.new('RGBA', (13, 28), widget_fg)
            slider_vert_prelight = Image.new('RGBA', (13, 28), active_bg2)

            self._im_trough[widget] = tkPhotoImage(width=15, height=15, master=self)
            self._im_trough[widget].put(" ".join(["{" + " ".join([bg] * 15) + "}"] * 15))
            self._im_slider_vert_active[widget] = PhotoImage(slider_vert_active,
                                                             master=self)
            self._im_slider_vert[widget] = PhotoImage(slider_vert,
                                                      master=self)
            self._im_slider_vert_prelight[widget] = PhotoImage(slider_vert_prelight,
                                                               master=self)
            self.style.element_create('%s.Vertical.Scrollbar.trough' % widget,
                                      'image', self._im_trough[widget])
            self.style.element_create('%s.Vertical.Scrollbar.thumb' % widget,
                                      'image', self._im_slider_vert[widget],
                                      ('pressed', '!disabled',
                                       self._im_slider_vert_active[widget]),
                                      ('active', '!disabled',
                                       self._im_slider_vert_prelight[widget]),
                                      border=6, sticky='ns')
            self.style.layout('%s.Vertical.TScrollbar' % widget,
                              [('%s.Vertical.Scrollbar.trough' % widget,
                                {'children': [('%s.Vertical.Scrollbar.thumb' % widget,
                                               {'expand': '1'})],
                                 'sticky': 'ns'})])
        # --- tree
        columns = {
            _('Summary'): ({'stretch': True, 'width': 300},
                           lambda: self._sort_by_desc(_('Summary'), False)),
            _('Place'): ({'stretch': True, 'width': 200},
                         lambda: self._sort_by_desc(_('Place'), False)),
            _('Category'): ({'stretch': False, 'width': 100},
                            lambda: self._sort_by_desc(_('Category'), False)),
            _('Start'): ({'stretch': False, 'width': 150},
                         lambda: self._sort_by_date(_('Start'), False)),
            _('End'): ({'stretch': False, 'width': 150},
                       lambda: self._sort_by_date(_("End"), False)),
            _('Recurring'): ({'stretch': False, 'width': 70},
                             lambda: self._sort_by_desc(_('Recurring'), False)),
            _('Next occurence'): ({'stretch': False, 'width': 150},
                                  lambda: self._sort_by_date(_('Next occurence'), False))

        }
        #Summary, Place, Category, Start, End, Is recurring, Next occurrence
        self.tree = Treeview(self, show="headings", columns=list(columns))
        for label, (col_prop, cmd) in columns.items():
            self.tree.column(label, **col_prop)
            self.tree.heading(label, text=label, anchor="w", command=cmd)
        self.tree.tag_configure('0', background='#ececec')
        self.tree.tag_configure('1', background='white')
        self.tree.tag_configure('outdated', foreground='red')

        scroll = AutoScrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        # --- toolbar
        toolbar = Frame(self)
        Button(toolbar, image='img_add', padding=1,
               command=self.add).pack(side="left", padx=4)
        Label(toolbar, text=_("Filter by")).pack(side="left", padx=4)
        Button(toolbar, text=_('Delete All Outdated'), padding=1,
               command=self.delete_outdated_events).pack(side="right", padx=4)
        # --- --- filters
        self.filter_col = Combobox(toolbar, state="readonly",
                                   values=("", _("Category"), _("Date"), _("Recurring")),
                                   exportselection=False)
        self.filter_col.pack(side="left", padx=4)
        # --- --- --- category
        self.filter_value = Combobox(toolbar, state="readonly",
                                        exportselection=False)
        # --- --- --- start date
        self.filter_date = Frame(toolbar)
        prop = {op: CONFIG.get('Calendar', op) for op in CONFIG.options('Calendar')}
        prop['font'] = "Liberation\ Sans 9"
        prop.update(selectforeground='white', selectbackground=active_bg)
        locale = CONFIG.get('General', 'locale')
        self.filter_date_start = DateEntry(self.filter_date, locale=locale, width=10,
                                           justify='center', **prop)
        self.filter_date_end = DateEntry(self.filter_date, locale=locale, width=10,
                                         justify='center', **prop)
        Label(self.filter_date, text=_('From')).pack(side='left')
        self.filter_date_start.pack(side='left', padx=4)
        Label(self.filter_date, text=_('to')).pack(side='left')
        self.filter_date_end.pack(side='left', padx=(4, 0))
        # --- grid
        toolbar.grid(row=0, columnspan=2, sticky='we', pady=4)
        self.tree.grid(row=1, column=0, sticky='eswn')
        scroll.grid(row=1, column=1, sticky='ns')

        # --- restore data
        data = {}
        self.events = {}
        try:
            with open(DATA_PATH, 'rb') as file:
                dp = Unpickler(file)
                data = dp.load()
        except Exception:
            l = [f for f in os.listdir(os.path.dirname(BACKUP_PATH)) if f.startswith('data.backup')]
            if l:
                l.sort(key=lambda x: int(x[11:]))
                shutil.copy(os.path.join(os.path.dirname(BACKUP_PATH), l[-1]),
                            DATA_PATH)
                with open(DATA_PATH, 'rb') as file:
                    dp = Unpickler(file)
                    data = dp.load()
        backup()
        now = datetime.now()
        self.min_date = now
        self.max_date = now
        for i, prop in enumerate(data):
            iid = prop.setdefault("iid", "I%.3i" % i)
            self.events[iid] = Event(self.scheduler, **prop)
            self.min_date = min(self.min_date, self.events[iid]['Start'])
            self.max_date = max(self.max_date, self.events[iid]['Start'])
            self.tree.insert('', 'end', iid, values=self.events[iid].values())
            tags = [str(self.tree.index(iid) % 2)]
            self.tree.item(iid, tags=tags)
            if not prop['Repeat']:
                for rid, d in list(prop['Reminders'].items()):
                    if d < now:
                        del self.events[iid]['Reminders'][rid]
        self.after_id = self.after(15 * 60 * 1000, self.check_outdated)

        # --- bindings
        self.bind_class("TCombobox", "<<ComboboxSelected>>",
                        self._clear_selection, add=True)
        self.bind_class("TCombobox", "<Control-a>",
                        self._select_all_entry)
        self.bind_class("TEntry", "<Control-a>",
                        self._select_all_entry)
        self.bind_class("Text", "<Control-a>",
                        self._select_all_text)
        self.tree.bind('<3>', self._post_menu)
        self.tree.bind('<1>', self._select)
        self.tree.bind('<Double-1>', self._edit_on_click)
        self.tree.bind('<Delete>', self._delete_events)
        self.menu.bind('<FocusOut>', lambda e: self.menu.unpost())
        self.filter_col.bind("<<ComboboxSelected>>", self.select_filter)
        self.filter_value.bind("<<ComboboxSelected>>", self.apply_filter_value)
        self.filter_date_end.bind("<<DateEntrySelected>>", self.apply_filter_date)
        self.filter_date_start.bind("<<DateEntrySelected>>", self._select_filter_date_start)

        # --- widgets
        self.widgets = {}
        self.widgets['Calendar'] = CalendarWidget(self)
        self.widgets['Events'] = EventWidget(self)
        self.widgets['Tasks'] = TaskWidget(self)
        self.widgets['Timer'] = Timer(self)
        self.widgets['Pomodoro'] = Pomodoro(self)

        self._setup_style()

        for item, widget in self.widgets.items():
            self.menu_widgets.add_checkbutton(label=_(item),
                                              command=lambda i=item: self.display_hide_widget(i))
            self.menu_widgets.set_item_value(_(item), widget.variable.get())
            add_trace(widget.variable, 'write',
                      lambda *args, i=item: self._menu_widgets_trace(i))

        self.icon.loop(self)
        self.tk.eval("""
apply {name {
    set newmap {}
    foreach {opt lst} [ttk::style map $name] {
        if {($opt eq "-foreground") || ($opt eq "-background")} {
            set newlst {}
            foreach {st val} $lst {
                if {($st eq "disabled") || ($st eq "selected")} {
                    lappend newlst $st $val
                }
            }
            if {$newlst ne {}} {
                lappend newmap $opt $newlst
            }
        } else {
            lappend newmap $opt $lst
        }
    }
    ttk::style map $name {*}$newmap
}} Treeview
        """)

        # react to scheduler --update-date in command line
        signal.signal(signal.SIGUSR1, self.update_date)
        # load .ics files from command line
        signal.signal(signal.SIGUSR2, self.load_ics_files_cmdline)

        # update selected date in calendar and event list every day
        self.scheduler.add_job(self.update_date,
                               CronTrigger(hour=0, minute=0, second=1),
                               jobstore='memo')

        self.scheduler.start()

        for filepath in files:
            self.load_ics_file(filepath)

        # --- ext sync [one way sync remote -> local]
        self.sync_after_id = ""
        self.ext_cal_sync()

    def _setup_style(self):
        # scrollbars
        for widget in ['Events', 'Tasks', 'Timer']:
            bg = CONFIG.get(widget, 'background')
            fg = CONFIG.get(widget, 'foreground')

            widget_bg = self.winfo_rgb(bg)
            widget_fg = tuple(round(c * 255 / 65535) for c in self.winfo_rgb(fg))
            active_bg = active_color(*widget_bg)
            active_bg2 = active_color(*active_color(*widget_bg, 'RGB'))

            slider_vert = Image.new('RGBA', (13, 28), active_bg)
            slider_vert.putalpha(self._slider_alpha)
            slider_vert_active = Image.new('RGBA', (13, 28), widget_fg)
            slider_vert_active.putalpha(self._slider_alpha)
            slider_vert_prelight = Image.new('RGBA', (13, 28), active_bg2)
            slider_vert_prelight.putalpha(self._slider_alpha)

            self._im_trough[widget].put(" ".join(["{" + " ".join([bg] * 15) + "}"] * 15))
            self._im_slider_vert_active[widget].paste(slider_vert_active)
            self._im_slider_vert[widget].paste(slider_vert)
            self._im_slider_vert_prelight[widget].paste(slider_vert_prelight)

        for widget in self.widgets.values():
            widget.update_style()

    def report_callback_exception(self, *args):
        err = ''.join(traceback.format_exception(*args))
        logging.error(err)
        if args[0] is not KeyboardInterrupt:
            showerror('Exception', str(args[1]), err)
        else:
            self.exit()

    def save(self):
        logging.info('Save event database')
        data = [ev.to_dict() for ev in self.events.values()]
        with open(DATA_PATH, 'wb') as file:
            pick = Pickler(file)
            pick.dump(data)

    def update_date(self, *args):
        """Update Calendar's selected day and Events' list."""
        self.widgets['Calendar'].update_date()
        self.widgets['Events'].display_evts()
        self.update_idletasks()

    def toggle_silent_mode(self):
        CONFIG.set('General', 'silent_mode',
                   str(self.icon.menu.get_item_value(_('Silent mode'))))

    # --- bindings
    def _select(self, event):
        if not self.tree.identify_row(event.y):
            self.tree.selection_remove(*self.tree.selection())

    def _edit_on_click(self, event):
        sel = self.tree.selection()
        if sel:
            sel = sel[0]
            self.edit(sel)

    def _delete_events(self, event):
        sel = self.tree.selection()
        if sel:
            ans = askokcancel(_("Confirmation"), _("Delete selected events (external events will not be removed)?"), parent=self)
            if ans:
                self.delete(*sel)

    # --- class bindings
    @staticmethod
    def _clear_selection(event):
        event.widget.selection_clear()

    @staticmethod
    def _select_all_entry(event):
        event.widget.selection_range(0, "end")
        return "break"

    @staticmethod
    def _select_all_text(event):
        event.widget.tag_add('sel', '1.0', 'end')
        return "break"

    # --- show / hide
    def _menu_widgets_trace(self, item):
        self.menu_widgets.set_item_value(_(item), self.widgets[item].variable.get())

    def display_hide_widget(self, item):
        value = self.menu_widgets.get_item_value(_(item))
        if value:
            self.widgets[item].show()
        else:
            self.widgets[item].hide()

    def hide(self):
        self._visible.set(False)
        self.withdraw()
        self.save()

    def show(self):
        self._visible.set(True)
        self.deiconify()

    def _visibility_trace(self, *args):
        self.icon.menu.set_item_value(_('Manager'), self._visible.get())

    def display_hide(self, toggle=False):
        value = self.icon.menu.get_item_value(_('Manager'))
        if toggle:
            value = not value
            self.icon.menu.set_item_value(_('Manager'), value)
        self._visible.set(value)
        if not value:
            self.withdraw()
            self.save()
        else:
            self.deiconify()

    # --- event management
    def event_add(self, event):
        iid = self.tree.insert('', 'end', iid=event.iid, values=event.values())
        if event.iid is None:
            event.iid = iid
        self.events[iid] = event
        self.min_date = min(self.min_date, event['Start'])
        self.max_date = max(self.max_date, event['Start'])
        self.tree.item(iid, tags=str(self.tree.index(iid) % 2))
        self.widgets['Calendar'].add_event(event)
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def event_configure(self, iid):
        self.tree.item(iid, values=self.events[iid].values())
        self.min_date = min(self.min_date, self.events[iid]['Start'])
        self.max_date = max(self.max_date, self.events[iid]['Start'])
        self.widgets['Calendar'].add_event(self.events[iid])
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def add(self, date=None):
        if date is not None:
            event = Event(self.scheduler, Start=date)
        else:
            event = Event(self.scheduler)
        Form(self, event, new=True)

    def delete_from_cal(self, iid, date):
        event = self.events[iid]
        if not event['Repeat']:
            self.delete(iid)
        else:
            opt = askoptions(_('Delete'), _('Delete recurring event:'),
                             _('This occurrence'),
                             _('This occurrence and the following ones'),
                             _('All occurences'))
            if opt == _('All occurences'):
                self.delete(iid)
            else:
                self.widgets['Calendar'].remove_event(event)
                if opt == _('This occurrence'):
                    start = event['Start']
                    event.exclude_date(date.replace(hour=start.hour, minute=start.minute))
                else:
                    event['Repeat']['Limit'] = 'until'
                    event['Repeat']['EndDate'] = date - timedelta(days=1)
                    event.create_rrule()
                    event.reminder_refresh_all()
                self.widgets['Events'].display_evts()
                self.widgets['Calendar'].add_event(event)

    def delete(self, *iids):
        min_ind = len(self.tree.get_children(''))
        for iid in iids:
            self.events[iid].reminder_remove_all()
            if self.events[iid]["ExtCal"]:
                continue # can only remove local reminders for external events
            index = self.tree.index(iid)
            min_ind = min(min_ind, index)
            self.tree.delete(iid)
            self.widgets['Calendar'].remove_event(self.events[iid])
            del self.events[iid]
        for k, item in enumerate(self.tree.get_children('')[min_ind:], min_ind):
            tags = [t for t in self.tree.item(item, 'tags')
                    if t not in ['1', '0']]
            tags.append(str(k % 2))
            self.tree.item(item, tags=tags)
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def edit_from_cal(self, iid, date):
        event = self.events[iid]
        if not event['Repeat']:
            self.edit(iid)
        else:
            opt = askoptions(_('Edit'), _('Edit recurring event:'),
                             _('This occurrence'),
                             _('This occurrence and the following ones'),
                             _('All occurences'))
            if opt == _('All occurences'):
                self.edit(iid)
            else:
                prop = event.to_dict()
                prop['iid'] = None
                start = event['Start']
                duration = event['End'] - start
                prop['Start'] = date.replace(hour=start.hour, minute=start.minute)
                prop['End'] = prop['Start'] + duration

                if opt == _('This occurrence'):
                    prop['Repeat'] = {}
                    event2 = Event(self.scheduler, **prop)
                    form = Form(self, event2, new=True)
                    self.wait_window(form)
                    if event2.iid:  # change was validated
                        self.widgets['Calendar'].remove_event(event)
                        event.exclude_date(date.replace(hour=start.hour, minute=start.minute))
                        self.widgets['Calendar'].add_event(event)
                        self.widgets['Events'].display_evts()
                else:
                    if prop['Repeat']['Limit'] == 'after':
                        end = event.get_last_date()
                        prop['Repeat']['Limit'] = 'until'
                        prop['Repeat']['EndDate'] = end
                    event2 = Event(self.scheduler, **prop)
                    form = Form(self, event2, new=True)
                    self.wait_window(form)
                    if event2.iid:  # change was validated
                        self.widgets['Calendar'].remove_event(event)
                        event['Repeat']['Limit'] = 'until'
                        event['Repeat']['EndDate'] = date - timedelta(days=1)
                        event.create_rrule()
                        event.reminder_refresh_all()
                        self.widgets['Calendar'].add_event(event)
                        self.widgets['Events'].display_evts()

    def edit(self, iid):
        try:
            self.widgets['Calendar'].remove_event(self.events[iid])
        except ValueError:
            return  # multiple clicks issue
        Form(self, self.events[iid])

    def check_outdated(self):
        """Check for outdated events every 15 min."""
        now = datetime.now()
        for iid, event in self.events.items():
            if not event['Repeat'] and event['Start'] < now:
                tags = list(self.tree.item(iid, 'tags'))
                if 'outdated' not in tags:
                    tags.append('outdated')
                self.tree.item(iid, tags=tags)
        self.after_id = self.after(15 * 60 * 1000, self.check_outdated)

    def delete_outdated_events(self):
        now = datetime.now()
        outdated = []
        for iid, prop in self.events.items():
            if prop['End'] < now:
                if not prop['Repeat']:
                    outdated.append(iid)
                elif prop['Repeat']['Limit'] != 'always':
                    end = prop['End']
                    enddate = datetime.fromordinal(prop['Repeat']['EndDate'].toordinal())
                    enddate.replace(hour=end.hour, minute=end.minute)
                    if enddate < now:
                        outdated.append(iid)
        self.delete(*outdated)
        logging.info('Deleted outdated events')

    def refresh_reminders(self):
        """
        Reschedule all reminders.

        Required when APScheduler is updated.
        """
        self.scheduler.remove_all_jobs("default")
        for event in self.events.values():
            event.reminder_refresh_all()
        logging.info('Refreshed reminders')

    # --- import export
    def _export_ical(self, filename):
        # TODO: timezone awareness, include VALARMs
        ical = icalendar.Calendar()
        ical.add('prodid', '-//j_4321//Scheduler Calendar//')
        ical.add('version', '2.0')
        ical.add('X-WR-CALNAME', 'My Scheduler Calendar')
        for event in self.events.values():
            ical.add_component(event.to_vevent())
        with open(filename, "wb") as file:
            file.write(ical.to_ical())

    def export_ical(self):
        filetypes = [('iCal', '*.ics'), (_("All files"), "*")]
        filename = asksaveasfilename(filetypes=filetypes,
                                     defaultextension=".ics",
                                     initialdir=os.path.expanduser("~"))
        if filename:
            self._export_ical(filename)


    def ext_cal_sync(self):
        """Update the external calendars in the local calendar."""
        active_cals = CONFIG.get("ExternalSync", "calendars").split(", ")
        while "" in active_cals:
            active_cals.remove("")
        nointernet = False
        for extcal in active_cals:
            url = CONFIG.get("ExternalCalendars", extcal)
            success, retry = self._load_ics_extsync(url, extcal)
            if success:
                logging.info(f"Synchronized external calendar {extcal} - {url}")
            elif retry:
                nointernet = True
        if len(active_cals): # schedule the next sync
            if nointernet:  # temporary lost internect connection, retry in 5 min
                self.sync_after_id = self.after(5*60*1000, self.ext_cal_sync)
            else:
                self.sync_after_id = self.after(CONFIG.getint("ExternalSync", "frequency")*60*1000,
                                                self.ext_cal_sync)

    def _load_ics_extsync(self, url, extcal):
        """
        Import events from icalendar data (sync).

        Return (success, retry)
        """
        try:
            data = requests.get(url)
            if data.ok:
                ical = icalendar.Calendar.from_ical(data.text)
            else:
                data.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Sync Error: {e}")
            return False, True  # no Internet, retry later
        except Exception as e:
            err = ''.join(traceback.format_exc())
            logging.error(err)
            showerror(_("Error"),
                      _("The import of the .ics data failed.") + f"\n\n{e}",
                      err)
            return False, False
        # use external calendar name as category
        category = extcal
        # old version of the events
        old_evts = [iid for iid, ev in self.events.items() if ev["ExtCal"] == extcal]  # to find deleted events in the updated version
        new_evts = []
        if not CONFIG.has_option("Categories", category):
            CONFIG.set("Categories", category, "white, #186CBE, 0")
            self.widgets['Calendar'].update_style()
            self.widgets['Events'].update_style()
        for component in ical.subcomponents:
            if component.name == "VEVENT":
                try:
                    event = Event.from_vevent(component, self.scheduler, category, category)
                except Exception:
                    logging.exception("Malformed Event Error")
                    continue
                iid = event.iid
                new_evts.append(iid)
                if iid not in self.events:
                    # create new event
                    self.tree.insert('', 'end', iid, values=event.values())
                    self.tree.item(iid, tags=str(self.tree.index(iid) % 2))
                else:
                    # update existing event (but keep local reminders)
                    dold = self.events[iid].to_dict()
                    dnew = event.to_dict()
                    del dold["Reminders"]
                    del dnew["Reminders"]
                    if dnew == dold:
                        event.reminder_remove_all()
                        del event
                        continue
                    # there were change
                    self.tree.item(iid, values=self.events[iid].values())
                    self.widgets['Calendar'].remove_event(self.events[iid])
                    self.events[iid].reminder_remove_all()
                    del self.events[iid]
                self.events[iid] = event
                self.widgets['Calendar'].add_event(event)
        # delete events deleted from the remote
        min_ind = len(self.tree.get_children(''))
        for iid in old_evts:
            if iid not in new_evts:
                min_ind = min(min_ind, self.tree.index(iid))
                self.tree.delete(iid)
                self.events[iid].reminder_remove_all()
                self.widgets['Calendar'].remove_event(self.events[iid])
                del self.events[iid]
        for k, item in enumerate(self.tree.get_children('')[min_ind:], min_ind):
            tags = [t for t in self.tree.item(item, 'tags')
                    if t not in ['1', '0']]
            tags.append(str(k % 2))
            self.tree.item(item, tags=tags)
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()
        return True, False

    def _load_ical(self, ical):
        """Import events from icalendar data."""
        # use iCalendar name as category
        category = ical.get('X-WR-CALNAME', CONFIG.options('Categories')[0]).lower()
        if not CONFIG.has_option("Categories", category):
            CONFIG.set("Categories", category, "white, #186CBE, 0")
            self.widgets['Calendar'].update_style()
            self.widgets['Events'].update_style()
        for component in ical.subcomponents:
            if component.name == "VEVENT":
                try:
                    event = Event.from_vevent(component, self.scheduler, category)
                except Exception:
                    logging.exception("Malformed Event Error")
                    continue
                iid = event.iid
                if iid not in self.events:
                    self.tree.insert('', 'end', iid, values=event.values())
                    self.tree.item(iid, tags=str(self.tree.index(iid) % 2))
                else:
                    self.tree.item(iid, values=self.events[iid].values())
                    self.widgets['Calendar'].remove_event(self.events[iid])
                    self.events[iid].reminder_remove_all()
                    del self.events[iid]
                self.events[iid] = event
                self.widgets['Calendar'].add_event(event)
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def load_ics_file(self, filename=None):
        if filename is None:
            filetypes = [('iCal', '*.ics'), (_("All files"), "*")]
            filename = askopenfilename(filetypes=filetypes,
                                       defaultextension=".ics",
                                       initialdir=os.path.expanduser("~"))
        if not filename:
            return False
        try:
            with open(filename, 'rb') as icalfile:
                ical = icalendar.Calendar.from_ical(icalfile.read())
        except Exception:
            err = ''.join(traceback.format_exc())
            logging.error(err)
            showerror(_("Error"), _("The import of the .ics file failed."), err)
            return False
        else:
            self._load_ical(ical)
            logging.info(f"Successfully loaded {filename}.")
            return True

    def load_ics_files_cmdline(self, *args):
        """
        Load .ics files from cmdline.

        The command line input is stored in OPENFILE_PATH
        """
        with open(OPENFILE_PATH) as file:
            files = file.read().splitlines()
        os.remove(OPENFILE_PATH)
        if not files:
            return
        success = []
        fail = []
        for filepath in files:
            if self.load_ics_file(filepath):
                success.append(filepath)
            else:
                fail.append(filepath)
        msg1, msg2 = "", ""
        if success:
            msg1 = _("Successfully loaded {file_list}.").format(file_list=', '.join(success))
            logging.info("Successfully loaded {file_list}.".format(file_list=', '.join(success)))
        if fail:
            msg2 = _("Failed to load {file_list}.").format(file_list=', '.join(fail))
            logging.info("Failed to load {file_list}.".format(file_list=', '.join(fail)))
        Popen(["notify-send", "-i", ICON_NOTIF, "Scheduler",
               f"{msg1} {msg2}"])

    def load_ics_url(self):

        def ok(ev=None):
            url = url_entry.get()
            if not url:
                top.destroy()
                return
            try:
                data = requests.get(url)
                if data.ok:
                    ical = icalendar.Calendar.from_ical(data.text)
                else:
                    data.raise_for_status()
            except Exception as e:
                err = ''.join(traceback.format_exc())
                logging.error(err)
                showerror(_("Error"),
                          _("The import of the .ics data failed.") + f"\n\n{e}",
                          err)
            else:
                self._load_ical(ical)
                logging.info(f"Successfully loaded {url}.")
            finally:
                top.destroy()

        top = Toplevel(self)
        Label(top, text=_("Import .ics data from url:")).pack(padx=4, pady=4)
        url_entry = Entry(top)
        url_entry.pack(fill="x", expand=True, padx=4, pady=4)
        Button(top, text=_("Import"), command=ok).pack(padx=4, pady=4)
        url_entry.focus_set()
        url_entry.bind("<Return>", ok)

    # --- sorting
    def _move_item(self, item, index):
        self.tree.move(item, "", index)
        tags = [t for t in self.tree.item(item, 'tags')
                if t not in ['1', '0']]
        tags.append(str(index % 2))
        self.tree.item(item, tags=tags)

    @staticmethod
    def to_datetime(date):
        if not date:
            return datetime.fromordinal(1)
        date_format = get_date_format("short", CONFIG.get("General", "locale")).pattern
        dayfirst = date_format.startswith("d")
        yearfirst = date_format.startswith("y")
        return parse(date, dayfirst=dayfirst, yearfirst=yearfirst)

    def _sort_by_date(self, col, reverse):
        l = [(self.to_datetime(self.tree.set(k, col)), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self._move_item(k, index)

        # reverse sort next time
        self.tree.heading(col,
                          command=lambda: self._sort_by_date(col, not reverse))

    def _sort_by_desc(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse, key=lambda x: x[0].lower())

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self._move_item(k, index)

        # reverse sort next time
        self.tree.heading(col,
                          command=lambda: self._sort_by_desc(col, not reverse))

    # --- filter
    def _reset_filter(self):
        for i, item in enumerate(self.events.keys()):
            self._move_item(item, i)

    def select_filter(self, event):
        col = self.filter_col.get()
        print(col, col == _("Date"))
        self._reset_filter()
        if not col:
            self.filter_value.pack_forget()
            self.filter_date.pack_forget()
        elif col == _("Date"):
            self.filter_date_start.set_date(self.min_date)
            self.filter_date_end.set_date(self.max_date)
            self.filter_value.pack_forget()
            self.filter_date.pack(side="left", padx=4)
        else:
            if col == _("Category"):
                self.filter_value.configure(values=sorted(CONFIG.options('Categories')))
            elif col == _("Recurring"):
                self.filter_value.configure(values=[_("Yes"), _("No")])
            self.filter_value.set("")
            self.filter_value.pack(side="left", padx=4)
            self.filter_date.pack_forget()

    def apply_filter_date(self, event):
        start_date = self.filter_date_start.get_date()
        end_date = self.filter_date_end.get_date()

        i = 0
        for item, evt in self.events.items():
            if evt.occurs_between(start_date, end_date):
                self._move_item(item, i)
                i += 1
            else:
                self.tree.detach(item)

    def _select_filter_date_start(self, event):
        self.filter_date_end.configure(mindate=self.filter_date_start.get_date())
        self.apply_filter_date(event)

    def apply_filter_value(self, event):
        col = self.filter_col.get()
        val = self.filter_value.get()
        items = list(self.events.keys())
        i = 0
        for item in items:
            if self.tree.set(item, col) == val:
                self._move_item(item, i)
                i += 1
            else:
                self.tree.detach(item)

    # --- manager's menu
    def _post_menu(self, event):
        self.right_click_iid = self.tree.identify_row(event.y)
        self.tree.selection_remove(*self.tree.selection())
        self.tree.selection_add(self.right_click_iid)
        if self.right_click_iid:
            try:
                self.menu.delete(_('Progress'))
            except TclError:
                pass
            state = self.events[self.right_click_iid]['Task']
            if state:
                self._task_var.set(state)
                if '%' in state:
                    self._img_dot = 'img_dot'
                else:
                    self._img_dot = tkPhotoImage(master=self)
                self.menu_task.entryconfigure(1, image=self._img_dot)
                self.menu.insert_cascade(0, menu=self.menu_task, label=_('Progress'))
            # external event cannot be deleted
            self.menu.entryconfigure(_("Delete"), state=["normal", "disabled"][bool(self.events[self.right_click_iid]['ExtCal'])])
            self.menu.tk_popup(event.x_root, event.y_root)

    def _delete_menu(self):
        if self.right_click_iid:
            self.delete(self.right_click_iid)

    def _edit_menu(self):
        if self.right_click_iid:
            self.edit(self.right_click_iid)

    def _set_progress(self):
        if self.right_click_iid:
            self.events[self.right_click_iid]['Task'] = self._task_var.get()
            self.widgets['Tasks'].display_tasks()
            if '%' in self._task_var.get():
                self._img_dot = 'img_dot'
            else:
                self._img_dot = tkPhotoImage(master=self)
            self.menu_task.entryconfigure(1, image=self._img_dot)

    # --- icon menu
    def exit(self):
        self.save()
        rep = self.widgets['Pomodoro'].stop(self.widgets['Pomodoro'].on)
        if not rep:
            return
        self.menu_eyes.quit()
        self.after_cancel(self.after_id)
        try:
            self.after_cancel(self.sync_after_id)
        except ValueError:
            pass
        try:
            self.scheduler.shutdown()
        except SchedulerNotRunningError:
            pass
        self.destroy()

    def settings(self):
        splash_supp = CONFIG.get('General', 'splash_supported')
        dialog = Settings(self)
        self.wait_window(dialog)
        self._setup_style()
        if splash_supp != CONFIG.get('General', 'splash_supported'):
            for widget in self.widgets.values():
                widget.update_position()
        # update ext cals
        active_cals = CONFIG.get('ExternalSync', "calendars").split(", ") + [""]
        to_delete = []
        for iid, ev in self.events.items():
            if ev["ExtCal"] not in active_cals:  # extcal was removed or deactivated
                to_delete.append(iid)
        self.delete(*to_delete)
        try:
            self.after_cancel(self.sync_after_id)
        except ValueError:
            pass
        self.ext_cal_sync()
        # refresh categories
        cats = CONFIG.options('Categories')
        default_cat = CONFIG.get('Calendar', 'default_category')
        for iid in self.tree.get_children():
            cat = self.tree.set(iid, 'Category')
            if cat not in cats:
                self.tree.set(iid, 'Category', default_cat)
                self.widgets['Calendar'].remove_event(self.events[iid])
                self.events[iid]['Category'] = default_cat
                self.widgets['Calendar'].add_event(self.events[iid])
        self.save()

    # --- week schedule
    def get_next_week_events(self):
        """Return events scheduled for the next 7 days """
        locale = CONFIG.get("General", "locale")
        next_ev = {}
        today = datetime.now().date()
        for d in range(7):
            day = today + timedelta(days=d)
            evts = self.widgets['Calendar'].get_events(day)
            if evts:
                evts = [self.events[iid] for iid in evts]
                evts.sort(key=lambda ev: ev.get_start_time())
                desc = []
                for ev in evts:
                    if ev["WholeDay"]:
                        date = ""
                    else:
                        date = "%s - %s " % (format_time(ev['Start'], locale=locale),
                                             format_time(ev['End'], locale=locale))
                    place = "(%s)" % ev['Place']
                    if place == "()":
                        place = ""
                    desc.append(("%s%s %s\n" % (date, ev['Summary'], place), ev['Description'], ev['Category']))
                next_ev[day.strftime('%A')] = desc
        return next_ev

    # --- tasks
    def get_tasks(self):
        # TODO: find events with repetition in the week
        # TODO: better handling of events on several days
        tasks = []
        for event in self.events.values():
            if event['Task']:
                tasks.append(event)
        return tasks
