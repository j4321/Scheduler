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


Task manager (main app)
"""

from tkinter import Tk, Menu, StringVar, TclError, BooleanVar
from tkinter import PhotoImage as tkPhotoImage
from tkinter.ttk import Button, Treeview, Style, Label, Combobox, Frame
from schedulerlib.messagebox import showerror
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError
from datetime import datetime, timedelta
from schedulerlib.constants import ICON48, ICON, IM_ADD, CONFIG, IM_DOT, JOBSTORE, \
    DATA_PATH, BACKUP_PATH, IM_SCROLL_ALPHA, active_color, backup, add_trace, \
    IM_SOUND, IM_MUTE, IM_SOUND_DIS, IM_MUTE_DIS, IM_CLOSED, IM_OPENED, \
    IM_CLOSED_SEL, IM_OPENED_SEL, ICON_FALLBACK, \
    format_date, format_datetime, format_time
from schedulerlib.trayicon import TrayIcon, SubMenu
from schedulerlib.form import Form
from schedulerlib.event import Event
from schedulerlib.widgets import EventWidget, Timer, TaskWidget, Pomodoro, CalendarWidget
from schedulerlib.settings import Settings
from schedulerlib.ttkwidgets import AutoScrollbar
from schedulerlib.about import About
from schedulerlib.eyes import Eyes
import os
import shutil
from pickle import Pickler, Unpickler
import logging
import traceback
from PIL import Image
from PIL.ImageTk import PhotoImage
from dateutil.parser import parse
from babel.dates import get_date_format


class EventScheduler(Tk):
    def __init__(self):
        Tk.__init__(self, className='Scheduler')
        logging.info('Start')
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self._visible = BooleanVar(self, False)
        self.withdraw()

        self.icon_img = PhotoImage(master=self, file=ICON48)
        self.iconphoto(True, self.icon_img)

        # --- systray icon
        self.icon = TrayIcon(ICON, fallback_icon_path=ICON_FALLBACK)

        # --- menu
        self.menu_widgets = SubMenu(parent=self.icon.menu)
        self.menu_eyes = Eyes(self.icon.menu, self)
        self.icon.menu.add_checkbutton(label=_('Manager'), command=self.display_hide)
        self.icon.menu.add_cascade(label=_('Widgets'), menu=self.menu_widgets)
        self.icon.menu.add_cascade(label=_("Eyes' rest"), menu=self.menu_eyes)
        self.icon.menu.add_command(label=_('Settings'), command=self.settings)
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
        # --- style
        self.style = Style(self)
        self.style.theme_use("clam")
        self.style.configure('title.TLabel', font='TkdefaultFont 10 bold')
        self.style.configure('title.TCheckbutton', font='TkdefaultFont 10 bold')
        self.style.configure('subtitle.TLabel', font='TkdefaultFont 9 bold')
        self.style.configure('white.TLabel', background='white')
        self.style.configure('border.TFrame', background='white', border=1, relief='sunken')
        self.style.configure("Treeview.Heading", font="TkDefaultFont")
        bgc = self.style.lookup("TButton", "background")
        fgc = self.style.lookup("TButton", "foreground")
        bga = self.style.lookup("TButton", "background", ("active",))
        self.style.map('TCombobox',
                       fieldbackground=[('readonly', 'white'),
                                        ('readonly', 'focus', 'white')],
                       background=[("disabled", "active", "readonly", bgc),
                                   ("!disabled", "active", "readonly", bga)],
                       foreground=[('readonly', '!disabled', fgc),
                                   ('readonly', '!disabled', 'focus', fgc),
                                   ('readonly', 'disabled', 'gray40'),
                                   ('readonly', 'disabled', 'focus', 'gray40')],
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
                       arrowcolor=[('disabled', self.style.lookup('TMenubutton', 'foreground', ['disabled']))])
        bg = self.style.lookup('TFrame', 'background', default='#ececec')
        self.configure(bg=bg)
        self.option_add('*Toplevel.background', bg)
        self.option_add('*Menu.background', bg)
        self.option_add('*Menu.tearOff', False)
        # toggle text
        self._open_image = PhotoImage(name='img_opened', file=IM_OPENED, master=self)
        self._closed_image = PhotoImage(name='img_closed', file=IM_CLOSED, master=self)
        self._open_image_sel = PhotoImage(name='img_opened_sel', file=IM_OPENED_SEL, master=self)
        self._closed_image_sel = PhotoImage(name='img_closed_sel', file=IM_CLOSED_SEL, master=self)
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
        self._im_sound = PhotoImage(master=self, file=IM_SOUND)
        self._im_mute = PhotoImage(master=self, file=IM_MUTE)
        self._im_sound_dis = PhotoImage(master=self, file=IM_SOUND_DIS)
        self._im_mute_dis = PhotoImage(master=self, file=IM_MUTE_DIS)
        self.style.element_create('mute', 'image', self._im_sound,
                                  ('selected', '!disabled', self._im_mute),
                                  ('selected', 'disabled', self._im_mute_dis),
                                  ('!selected', 'disabled', self._im_sound_dis),
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
        for widget in ['Events', 'Tasks']:
            bg = CONFIG.get(widget, 'background', fallback='gray10')
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
        columns = {_('Summary'): ({'stretch': True, 'width': 300}, lambda: self._sort_by_desc(_('Summary'), False)),
                   _('Place'): ({'stretch': True, 'width': 200}, lambda: self._sort_by_desc(_('Place'), False)),
                   _('Start'): ({'stretch': False, 'width': 150}, lambda: self._sort_by_date(_('Start'), False)),
                   _('End'): ({'stretch': False, 'width': 150}, lambda: self._sort_by_date(_("End"), False)),
                   _('Category'): ({'stretch': False, 'width': 100}, lambda: self._sort_by_desc(_('Category'), False))}
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
        self.img_plus = PhotoImage(master=self, file=IM_ADD)
        Button(toolbar, image=self.img_plus, padding=1,
               command=self.add).pack(side="left", padx=4)
        Label(toolbar, text=_("Filter by")).pack(side="left", padx=4)
        # --- TODO: add filter by start date (after date)
        self.filter_col = Combobox(toolbar, state="readonly",
                                   # values=("",) + self.tree.cget('columns')[1:],
                                   values=("", _("Category")),
                                   exportselection=False)
        self.filter_col.pack(side="left", padx=4)
        self.filter_val = Combobox(toolbar, state="readonly",
                                   exportselection=False)
        self.filter_val.pack(side="left", padx=4)
        Button(toolbar, text=_('Delete All Outdated'), padding=1,
               command=self.delete_outdated_events).pack(side="right", padx=4)

        # --- grid
        toolbar.grid(row=0, columnspan=2, sticky='we', pady=4)
        self.tree.grid(row=1, column=0, sticky='eswn')
        scroll.grid(row=1, column=1, sticky='ns')

        # --- restore data
        data = {}
        self.events = {}
        self.nb = 0
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
        self.nb = len(data)
        backup()
        now = datetime.now()
        for i, prop in enumerate(data):
            iid = str(i)
            self.events[iid] = Event(self.scheduler, iid=iid, **prop)
            self.tree.insert('', 'end', iid, values=self.events[str(i)].values())
            tags = [str(self.tree.index(iid) % 2)]
            self.tree.item(iid, tags=tags)
            if not prop['Repeat']:
                for rid, d in list(prop['Reminders'].items()):
                    if d < now:
                        del self.events[iid]['Reminders'][rid]
        self.after_id = self.after(15 * 60 * 1000, self.check_outdated)

        # --- bindings
        self.bind_class("TCombobox", "<<ComboboxSelected>>",
                        self.clear_selection, add=True)
        self.bind_class("TCombobox", "<Control-a>",
                        self.select_all)
        self.bind_class("TEntry", "<Control-a>",
                        self.select_all)
        self.tree.bind('<3>', self._post_menu)
        self.tree.bind('<1>', self._select)
        self.tree.bind('<Double-1>', self._edit_on_click)
        self.menu.bind('<FocusOut>', lambda e: self.menu.unpost())
        self.filter_col.bind("<<ComboboxSelected>>", self.update_filter_val)
        self.filter_val.bind("<<ComboboxSelected>>", self.apply_filter)

        # --- widgets
        self.widgets = {}
        prop = {op: CONFIG.get('Calendar', op) for op in CONFIG.options('Calendar')}
        self.widgets['Calendar'] = CalendarWidget(self,
                                                  locale=CONFIG.get('General', 'locale'),
                                                  **prop)
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
        self.scheduler.start()

    def _setup_style(self):
        # --- scrollbars
        for widget in ['Events', 'Tasks']:
            bg = CONFIG.get(widget, 'background', fallback='gray10')
            fg = CONFIG.get(widget, 'foreground', fallback='white')

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
        showerror('Exception', str(args[1]), err, parent=self)

    # --- class bindings
    @staticmethod
    def clear_selection(event):
        combo = event.widget
        combo.selection_clear()

    @staticmethod
    def select_all(event):
        event.widget.selection_range(0, "end")
        return "break"

    # --- filter
    def update_filter_val(self, event):
        col = self.filter_col.get()
        self.filter_val.set("")
        if col:
            l = set()
            for k in self.events:
                l.add(self.tree.set(k, col))

            self.filter_val.configure(values=tuple(l))
        else:
            self.filter_val.configure(values=[])
            self.apply_filter(event)

    def apply_filter(self, event):
        col = self.filter_col.get()
        val = self.filter_val.get()
        items = list(self.events.keys())
        if not col:
            for item in items:
                self.tree.move(item, "", int(item))
        else:
            for item in items:
                if self.tree.set(item, col) == val:
                    self.tree.move(item, "", int(item))
                else:
                    self.tree.detach(item)

    def check_outdated(self):
        """check for outdated events every 15 min """
        now = datetime.now()
        for iid, event in self.events.items():
            if not event['Repeat'] and event['Start'] < now:
                tags = list(self.tree.item(iid, 'tags'))
                if 'outdated' not in tags:
                    tags.append('outdated')
                self.tree.item(iid, tags=tags)
        self.after_id = self.after(15 * 60 * 1000, self.check_outdated)

    def _select(self, event):
        if not self.tree.identify_row(event.y):
            self.tree.selection_remove(*self.tree.selection())

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

    def _move_item(self, item, index):
        self.tree.move(item, "", index)
        tags = [t for t in self.tree.item(item, 'tags')
                if t not in ['1', '0']]
        tags.append(str(index % 2))
        self.tree.item(item, tags=tags)

    @staticmethod
    def to_datetime(date):
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
                    self._img_dot = PhotoImage(master=self, file=IM_DOT)
                else:
                    self._img_dot = tkPhotoImage(master=self)
                self.menu_task.entryconfigure(1, image=self._img_dot)
                self.menu.insert_cascade(0, menu=self.menu_task, label=_('Progress'))
            self.menu.tk_popup(event.x_root, event.y_root)

    def _delete_menu(self):
        if self.right_click_iid:
            self.delete(self.right_click_iid)

    def _set_progress(self):
        if self.right_click_iid:
            self.events[self.right_click_iid]['Task'] = self._task_var.get()
            self.widgets['Tasks'].display_tasks()
            if '%' in self._task_var.get():
                self._img_dot = PhotoImage(master=self, file=IM_DOT)
            else:
                self._img_dot = tkPhotoImage(master=self)
            self.menu_task.entryconfigure(1, image=self._img_dot)

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
        for item in outdated:
            self.delete(item)

    def delete(self, iid):
        index = self.tree.index(iid)
        self.tree.delete(iid)
        for k, item in enumerate(self.tree.get_children('')[index:]):
            tags = [t for t in self.tree.item(item, 'tags')
                    if t not in ['1', '0']]
            tags.append(str((index + k) % 2))
            self.tree.item(item, tags=tags)

        self.events[iid].reminder_remove_all()
        self.widgets['Calendar'].remove_event(self.events[iid])
        del(self.events[iid])
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def edit(self, iid):
        self.widgets['Calendar'].remove_event(self.events[iid])
        Form(self, self.events[iid])

    def _edit_menu(self):
        if self.right_click_iid:
            self.edit(self.right_click_iid)

    def _edit_on_click(self, event):
        sel = self.tree.selection()
        if sel:
            sel = sel[0]
            self.edit(sel)

    def add(self, date=None):
        iid = str(self.nb + 1)
        if date is not None:
            event = Event(self.scheduler, iid=iid, Start=date)
        else:
            event = Event(self.scheduler, iid=iid)
        Form(self, event, new=True)

    def event_add(self, event):
        self.nb += 1
        iid = str(self.nb)
        self.events[iid] = event
        self.tree.insert('', 'end', iid, values=event.values())
        self.tree.item(iid, tags=str(self.tree.index(iid) % 2))
        self.widgets['Calendar'].add_event(event)
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def event_configure(self, iid):
        self.tree.item(iid, values=self.events[iid].values())
        self.widgets['Calendar'].add_event(self.events[iid])
        self.widgets['Events'].display_evts()
        self.widgets['Tasks'].display_tasks()
        self.save()

    def save(self):
        logging.info('Save event database')
        data = [ev.to_dict() for ev in self.events.values()]
        with open(DATA_PATH, 'wb') as file:
            pick = Pickler(file)
            pick.dump(data)

    def exit(self):
        self.save()
        rep = self.widgets['Pomodoro'].stop(self.widgets['Pomodoro'].on)
        if not rep:
            return
        self.menu_eyes.quit()
        self.after_cancel(self.after_id)
        try:
            self.scheduler.shutdown()
        except SchedulerNotRunningError:
            pass
        self.destroy()

    def settings(self):
        dialog = Settings(self)
        self.wait_window(dialog)
        self._setup_style()

    def get_next_week_events(self):
        """return events scheduled for the next 7 days """
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
                    dt = ev['End'].date() - ev['Start'].date()
                    if ev["WholeDay"]:
                        if dt.days == 0:
                            date = ""
                        else:
                            date = "%s - %s " % (format_date(day, locale=locale),
                                                 format_date(day + dt, locale=locale))
                    else:
                        if dt.days == 0:
                            date = "%s - %s " % (format_time(ev['Start'], locale=locale),
                                                 format_time(ev['End'], locale=locale))
                        else:
                            start = datetime.combine(day, ev['Start'].time())
                            end = datetime.combine(day + dt, ev['End'].time())
                            date = "%s - %s " % (format_datetime(start, locale=locale),
                                                 format_date(end, locale=locale))
                    place = "(%s)" % ev['Place']
                    if place == "()":
                        place = ""
                    desc.append(("%s%s %s\n" % (date, ev['Summary'], place), ev['Description']))
                next_ev[day.strftime('%A')] = desc
        return next_ev

    def get_tasks(self):
        # TODO: find events with repetition in the week
        # TODO: better handling of events on several days
        tasks = []
        for event in self.events.values():
            if event['Task']:
                tasks.append(event)
        return tasks
