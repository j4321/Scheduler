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


Task manager (main app)
"""

from tkinter import Tk, PhotoImage, Menu, StringVar, TclError, Toplevel
from tkinter.ttk import Button, Treeview, Style, Label, Combobox, Frame, Entry, Checkbutton
from schedulerlib.messagebox import showerror
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError
from datetime import datetime, timedelta
from schedulerlib.constants import ICON, PLUS, CONFIG, DOT, JOBSTORE, backup,\
    DATA_PATH, BACKUP_PATH, SYNC_PWD
from schedulerlib.tktray import Icon
from schedulerlib.form import Form
from schedulerlib.event import Event
from schedulerlib.event_widget import EventWidget
from schedulerlib.timer_widget import Timer
from schedulerlib.task_widget import TaskWidget
from schedulerlib.calendar_widget import CalendarWidget
from schedulerlib.ttkwidgets import AutoScrollbar
from schedulerlib.about import About
from schedulerlib.messagebox import showinfo
from schedulerlib.sync import download_from_server, check_login_info, warn_exist_remote
import os
import time
import shutil
from pickle import Pickler, Unpickler
import logging
import traceback


def _(text):
    return text


#TODO: fix reminder duplication

class EventScheduler(Tk):
    def __init__(self):
        Tk.__init__(self)
        logging.info('Start')
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.display_hide)

        self.icon_img = PhotoImage(master=self, file=ICON)
        self.iconphoto(True, self.icon_img)
        self.icon = Icon(self, image=self.icon_img)
        menu = Menu(self.icon.menu, tearoff=False)
        self.icon.menu.add_cascade(label='Widgets', menu=menu)
        self.icon.menu.add_command(label='About', command=lambda: About(self))
        self.icon.menu.add_command(label='Quit', command=self.exit)
        self.icon.bind('<1>', self.display_hide)

        self.menu = Menu(self, tearoff=False)
        self.menu.add_command(label='Edit', command=self._edit_menu)
        self.menu.add_command(label='Delete', command=self._delete_menu)
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
            self.menu_task.add_radiobutton(label=state, value=state,
                                           variable=self._task_var,
                                           command=self._set_progress)
        self._img_dot = PhotoImage(master=self)
        self.menu_task.insert_cascade(1, menu=menu_in_progress,
                                      compound='left',
                                      label='In Progress',
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
        self.style.configure("Treeview.Heading", font="TkDefaultFont")
        self.configure(bg=self.style.lookup('TFrame', 'background'))
        self.style.map("TCombobox", fieldbackground=[("readonly", "white")],
                       foreground=[("readonly", "black")])

        # --- tree
        self.tree = Treeview(self, show="headings",
                             columns=('Summary', 'Place', 'Start', 'End', 'Category'))
        self.tree.column('Summary', stretch=True, width=300)
        self.tree.column('Place', stretch=True, width=200)
        self.tree.column('Start', width=150, stretch=False)
        self.tree.column('End', width=150, stretch=False)
        self.tree.column('Category', width=100)
        self.tree.heading('Summary', text='Summary', anchor="w",
                          command=lambda: self._sort_by_desc('Summary', False))
        self.tree.heading('Place', text='Place', anchor="w",
                          command=lambda: self._sort_by_desc('Place', False))
        self.tree.heading('Start', text='Start', anchor="w",
                          command=lambda: self._sort_by_date('Start', False))
        self.tree.heading('End', text='End', anchor="w",
                          command=lambda: self._sort_by_date('End', False))
        self.tree.heading('Category', text='Category', anchor="w",
                          command=lambda: self._sort_by_desc('Category', False))

        self.tree.tag_configure('0', background='#ececec')
        self.tree.tag_configure('1', background='white')
        self.tree.tag_configure('outdated', foreground='red')

        scroll = AutoScrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        # --- toolbar
        toolbar = Frame(self)
        self.img_plus = PhotoImage(master=self, file=PLUS)
        Button(toolbar, image=self.img_plus, padding=1,
               command=self.add).pack(side="left", padx=4)
        Label(toolbar, text="Filter by").pack(side="left", padx=4)
        # --- TODO: add filter by start date (after date)
        self.filter_col = Combobox(toolbar, state="readonly",
                                   # values=("",) + self.tree.cget('columns')[1:],
                                   values=("", "Category"),
                                   exportselection=False)
        self.filter_col.pack(side="left", padx=4)
        self.filter_val = Combobox(toolbar, state="readonly",
                                   exportselection=False)
        self.filter_val.pack(side="left", padx=4)

        # --- grid
        toolbar.grid(row=0, columnspan=2, sticky='w', pady=4)
        self.tree.grid(row=1, column=0, sticky='eswn')
        scroll.grid(row=1, column=1, sticky='ns')

        # --- Sync

        if CONFIG.getboolean("Sync", "on"):
            try:
                with open(SYNC_PWD) as f:
                    self.password = f.read().strip()
            except FileNotFoundError:
                self.password = ""

            if not self.password:
                self.get_server_pwd()

            if self.password:
                while (not check_login_info(self.password)) and self.password:
                    self.get_server_login()
                if self.password:
                    self.configure(cursor="watch")
                    res = download_from_server(self.password)
                    if not res:
                        showinfo(_("Information"),
                                 _("There was an error during the synchronization so synchronization has been disabled."))
                        CONFIG.set("Sync", "on", "False")
            else:
                showinfo(_("Information"),
                         _("No password has been given so synchronization has been disabled."))
                CONFIG.set("Sync", "on", "False")
        self.time = time.time()

        # --- restore data
        data = {}
        self.events = {}
        self.nb = 0
        try:
            with open(DATA_PATH, 'rb') as file:
                dp = Unpickler(file)
                data = dp.load()
        except Exception:
            l = os.listdir(os.path.dirname(BACKUP_PATH))
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
            if not prop['Repeat'] and prop['Start'] < now:
                tags.append('outdated')
            self.tree.item(iid, tags=tags)

        self.after_id = self.after(15 * 60 * 1000, self.check_outdated)

        # --- bindings
        self.bind_class("TCombobox", "<<ComboboxSelected>>",
                        self.clear_selection, add=True)
        self.tree.bind('<3>', self._post_menu)
        self.tree.bind('<1>', self._select)
        self.tree.bind('<Double-1>', self._edit_on_click)
        self.menu.bind('<FocusOut>', lambda e: self.menu.unpost())
        self.filter_col.bind("<<ComboboxSelected>>", self.update_filter_val)
        self.filter_val.bind("<<ComboboxSelected>>", self.apply_filter)

        # --- widgets
        prop = {op: CONFIG.get('Calendar', op) for op in CONFIG.options('Calendar')}
        self.cal_widget = CalendarWidget(self,
                                         locale=CONFIG.get('General', 'locale'),
                                         **prop)
        self.events_widget = EventWidget(self)
        self.tasks_widget = TaskWidget(self)
        self.timer_widget = Timer(self)

        menu.add_checkbutton(label='Calendar', command=self.display_hide_cal,
                             variable=self.cal_widget.variable)
        menu.add_checkbutton(label='Events', command=self.display_hide_events,
                             variable=self.events_widget.variable)
        menu.add_checkbutton(label='Tasks', command=self.display_hide_tasks,
                             variable=self.tasks_widget.variable)
        menu.add_checkbutton(label='Timer', command=self.display_hide_timer,
                             variable=self.timer_widget.variable)

        self.scheduler.start()


    def report_callback_exception(self, *args):
        err = ''.join(traceback.format_exception(*args))
        logging.error(err)
        showerror('Exception', str(args[1]), err, parent=self)

    # --- class bindings
    def clear_selection(self, event):
        combo = event.widget
        combo.selection_clear()

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

    def display_hide_tasks(self):
        if self.tasks_widget.winfo_ismapped():
            self.tasks_widget.withdraw()
        else:
            self.tasks_widget.deiconify()

    def display_hide_events(self):
        if self.events_widget.winfo_ismapped():
            self.events_widget.withdraw()
        else:
            self.events_widget.deiconify()

    def display_hide_timer(self):
        if self.timer_widget.winfo_ismapped():
            self.timer_widget.withdraw()
        else:
            self.timer_widget.deiconify()

    def display_hide_cal(self):
        if self.cal_widget.winfo_ismapped():
            self.cal_widget.withdraw()
        else:
            self.cal_widget.deiconify()

    def display_hide(self, event=None):
        if self.winfo_ismapped():
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

    def _sort_by_date(self, col, reverse):
        l = [(self.events[k][col], k) for k in self.tree.get_children('')]
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
                self.menu.delete('Progress')
            except TclError:
                pass
            state = self.events[self.right_click_iid]['Task']
            if state:
                self._task_var.set(state)
                if '%' in state:
                    self._img_dot = PhotoImage(master=self, file=DOT)
                else:
                    self._img_dot = PhotoImage(master=self)
                self.menu_task.entryconfigure(1, image=self._img_dot)
                self.menu.insert_cascade(0, menu=self.menu_task, label='Progress')
            self.menu.tk_popup(event.x_root, event.y_root)

    def _delete_menu(self):
        if self.right_click_iid:
            self.delete(self.right_click_iid)

    def _set_progress(self):
        if self.right_click_iid:
            self.events[self.right_click_iid]['Task'] = self._task_var.get()
            self.tasks_widget.display_tasks()
            if '%' in self._task_var.get():
                self._img_dot = PhotoImage(master=self, file=DOT)
            else:
                self._img_dot = PhotoImage(master=self)
            self.menu_task.entryconfigure(1, image=self._img_dot)

    def delete(self, iid):
        index = self.tree.index(iid)
        self.tree.delete(iid)
        for k, item in enumerate(self.tree.get_children('')[index:]):
            tags = [t for t in self.tree.item(item, 'tags')
                    if t not in ['1', '0']]
            tags.append(str((index + k) % 2))
            self.tree.item(item, tags=tags)

        self.events[iid].reminder_remove_all()
        self.cal_widget.remove_event(self.events[iid])
        del(self.events[iid])
        self.events_widget.display_evts()
        self.tasks_widget.display_tasks()
        self.save()

    def edit(self, iid):
        self.cal_widget.remove_event(self.events[iid])
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
        self.cal_widget.add_event(event)
        self.events_widget.display_evts()
        self.tasks_widget.display_tasks()
        self.save()

    def event_configure(self, iid):
        self.tree.item(iid, values=self.events[iid].values())
        self.cal_widget.add_event(self.events[iid])
        self.events_widget.display_evts()
        self.tasks_widget.display_tasks()
        self.save()

    def save(self):
        logging.info('Save event database')
        data = [ev.to_dict() for ev in self.events.values()]
        with open(DATA_PATH, 'wb') as file:
            pick = Pickler(file)
            pick.dump(data)

    def exit(self):
        self.save()
        self.after_cancel(self.after_id)
        try:
            self.scheduler.shutdown()
        except SchedulerNotRunningError:
            pass
        self.destroy()

    def get_next_week_events(self):
        """return events scheduled for the next 7 days """
        next_ev = {}
        today = datetime.now().date()
#        for event in self.events.values():
#            dt = event['Start'].date() - today
#            if dt.days >= 0 and dt.days < 7:
#                next_ev.append(event)
        for d in range(7):
            day = today + timedelta(days=d)
            evts = self.cal_widget.get_events(day)
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
                            start = day.strftime('%x')
                            end = (day + dt).strftime('%x')
                            date = "%s - %s " % (start, end)
                    else:
                        start = ev['Start'].strftime('%H:%M')
                        end = ev['End'].strftime('%H:%M')
                        if dt.days == 0:
                            date = "%s - %s " % (start, end)
                        else:
                            date = "%s %s - %s %s " % (day.strftime('%x'),
                                                       start,
                                                       (day + dt).strftime('%x'),
                                                       end)
                    place = "(%s)" % ev['Place']
                    if place == "()":
                        place = ""
                    desc.append(("%s%s %s\n" % (date, ev['Summary'], place), ev['Description']))
                next_ev[day.strftime('%A')] = desc
        return next_ev

    def get_tasks(self):
        # --- TODO: find events with repetition in the week
        # --- TODO: better handling of events on several days
        tasks = []
        for event in self.events.values():
            if event['Task']:
                tasks.append(event)
        return tasks

    def get_server_pwd(self):
        def ok(event=None):
            self.password = pwd.get()
            top.destroy()
            self.update_idletasks()

        top = Toplevel(self)
        top.title(_("Sync"))
        top.grab_set()
        top.resizable(False, False)
        pwd = Entry(top, show="*", justify="center")

        Label(top, text="Server password").pack(padx=4, pady=4)
        pwd.pack(padx=4, pady=4)
        Button(top, text=_("Connect"), command=ok).pack(padx=4, pady=4)
        pwd.bind("<Return>", ok)
        pwd.focus_set()
        self.wait_window(top)

    def get_server_login(self):
        def ok(event=None):
            if "selected" in ch.state():
                username = user.get()
                CONFIG.set("Sync", "username", username)
                self.password = pwd.get()
            else:
                CONFIG.set("Sync", "on", "False")
                self.password = ""
            top.destroy()

        def toggle():
            if "selected" in ch.state():
                state = "!disabled"
            else:
                state = "disabled"
            user.state((state,))
            pwd.state((state,))

        top = Toplevel(self)
        top.title(_("Sync"))
        top.grab_set()
        top.resizable(False, False)

        user = Entry(top)
        user.insert(0, CONFIG.get("Sync", "username"))
        pwd = Entry(top, show="*")

        ch = Checkbutton(top, text=_("Synchronize notes with server"), command=toggle)
        ch.state(("selected",))
        ch.grid(row=0, columnspan=2, padx=4, pady=4, sticky="w")
        Label(top, text=_("Username")).grid(row=1, column=0, padx=4, pady=4,
                                            sticky='e')
        Label(top, text=_("Password")).grid(row=2, column=0, padx=4, pady=4,
                                            sticky='e')
        user.grid(row=1, column=1, padx=4, pady=4)
        pwd.grid(row=2, column=1, padx=4, pady=4)
        Button(top, text="Ok", command=ok).grid(row=3, columnspan=2)
        pwd.bind("<Return>", ok)
        pwd.focus_set()
        self.wait_window(top)

    def set_password(self, pwd, sync_activated):
        self.password = pwd
        if CONFIG.getboolean("Sync", "on"):
            if not self.password:
                CONFIG.set("Sync", "on", "False")
                showinfo(_("Information"),
                         _("No password has been given so synchronization has been disabled."))
            while (not check_login_info(self.password)) and self.password:
                self.get_server_login()
            if self.password and sync_activated:
                res = warn_exist_remote(self.password)
                if res == "download":
                    self.reinit()

    def reinit(self):
        try:
            self.scheduler.shutdown()
        except SchedulerNotRunningError:
            pass
        self.scheduler = BackgroundScheduler(coalesce=False,
                                             misfire_grace_time=86400)
        self.scheduler.add_jobstore('sqlalchemy',
                                    url='sqlite:///%s' % JOBSTORE)
        self.tree.delete(*(self.tree.get_children('')))
        data = {}
        self.events = {}
        self.nb = 0
        try:
            with open(DATA_PATH, 'rb') as file:
                dp = Unpickler(file)
                data = dp.load()
        except Exception:
            l = os.listdir(os.path.dirname(BACKUP_PATH))
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
            if not prop['Repeat'] and prop['Start'] < now:
                tags.append('outdated')
            self.tree.item(iid, tags=tags)

    def get_password(self):
        return self.password

    def get_time(self):
        return self.time
