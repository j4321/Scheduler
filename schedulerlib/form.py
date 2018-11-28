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


Task editor
"""

from tkinter import Toplevel, Text, Spinbox, BooleanVar, StringVar
from tkinter.ttk import Entry, Label, Button, Frame, Style, Combobox
from tkinter.ttk import Radiobutton, Checkbutton, Notebook
from schedulerlib.constants import IM_BELL, IM_MOINS, CONFIG, \
    TASK_REV_TRANSLATION, FREQ_REV_TRANSLATION, only_nb
from schedulerlib.ttkcalendar import DateEntry, get_calendar
from schedulerlib.ttkwidgets import LabelFrame
from datetime import timedelta, time, datetime
from PIL.ImageTk import PhotoImage


class Form(Toplevel):
    def __init__(self, master, event, new=False):
        Toplevel.__init__(self, master)
        self.minsize(410, 402)
        if master.winfo_ismapped():
            self.transient(master)
        self.protocol('WM_DELETE_WINDOW', self.cancel)

        self._only_nb = self.register(only_nb)

        self.event = event
        if new:
            self.title(_('New Event'))
        else:
            self.title(_('Edit Event'))
        self._new = new
        self._task = BooleanVar(self, bool(event['Task']))
        self._whole_day = BooleanVar(self, event['WholeDay'])

        # --- style
        style = Style(self)
        active_bg = style.lookup('TEntry', 'selectbackground', ('focus',))

        self.alarms = []

        notebook = Notebook(self)
        notebook.pack(fill='both', expand=True)
        Button(self, text=_('Ok'), command=self.ok).pack(pady=(10, 6), padx=4)

        # --- event settings
        frame_event = Frame(notebook)
        notebook.add(frame_event, text=_('Event'), sticky='eswn', padding=4)
        frame_event.columnconfigure(1, weight=1)
        frame_event.rowconfigure(5, weight=1)

        self.img_moins = PhotoImage(master=self, file=IM_MOINS)
        self.img_bell = PhotoImage(master=self, file=IM_BELL)
        Label(frame_event, text=_('Summary')).grid(row=0, column=0, padx=4, pady=6, sticky='e')
        Label(frame_event, text=_('Place')).grid(row=1, column=0, padx=4, pady=6, sticky='e')
        Label(frame_event, text=_('Start')).grid(row=2, column=0, padx=4, pady=6, sticky='e')
        self._end_label = Label(frame_event, text=_('End'))
        self._end_label.grid(row=3, column=0, padx=4, pady=6, sticky='e')
        frame_task = Frame(frame_event)
        frame_task.grid(row=4, column=1, padx=4, pady=6, sticky='w')
        Label(frame_event, text=_('Description')).grid(row=5, column=0, padx=4, pady=6, sticky='e')
        Label(frame_event, text=_('Category')).grid(row=6, column=0, padx=4, pady=6, sticky='e')
        Button(frame_event, image=self.img_bell, command=self.add_reminder,
               padding=0).grid(row=7, column=0, padx=4, pady=6, sticky='en')

        self.summary = Entry(frame_event, width=35)
        self.summary.insert(0, self.event['Summary'])
        self.summary.grid(row=0, column=1, padx=4, pady=6, sticky='ew')
        self.place = Entry(frame_event, width=35)
        self.place.insert(0, self.event['Place'])
        self.place.grid(row=1, column=1, padx=4, pady=6, sticky='ew')
        frame_start = Frame(frame_event)
        frame_start.grid(row=2, column=1, padx=4, pady=6, sticky='w')
        frame_end = Frame(frame_event)
        frame_end.grid(row=3, column=1, padx=4, pady=6, sticky='w')
        txt_frame = Frame(frame_event, style='txt.TFrame', border=1, relief='sunken')
        self.desc = Text(txt_frame, width=35, height=4, highlightthickness=0,
                         relief='flat',
                         selectbackground=active_bg)
        self.desc.insert('1.0', self.event['Description'])
        self.desc.pack(fill='both', expand=True)
        txt_frame.grid(row=5, column=1, padx=4, pady=6, sticky='ewsn')
        cats = list(CONFIG.options('Categories'))
        width = max([len(cat) for cat in cats])
        self.category = Combobox(frame_event, width=width + 2, values=cats,
                                 state='readonly')
        self.category.set(event['Category'])
        self.category.grid(row=6, column=1, padx=4, pady=6, sticky='w')
        self.frame_alarms = Frame(frame_event)
        self.frame_alarms.grid(row=7, column=1, sticky='w')

        # --- *--- task
        Checkbutton(frame_task, text=_('Task'), command=self._change_label,
                    variable=self._task).pack(side='left')

        self.task_progress = Combobox(frame_task, state='readonly', width=9,
                                      values=(_('Pending'), _('In Progress'),
                                              _('Completed'), _('Cancelled')))
        self.task_progress.pack(side='left', padx=(8, 4))
        self.in_progress = Combobox(frame_task, state='readonly', width=5,
                                    values=['{}%'.format(i) for i in range(0, 110, 10)])
        self.in_progress.pack(side='left', padx=4)
        if not event['Task']:
            self.task_progress.set(_('Pending'))
            self.in_progress.set('0%')
        elif '%' in event['Task']:
            self.task_progress.set(_('In Progress'))
            self.in_progress.set(event['Task'])
        else:
            self.task_progress.set(_(event['Task']))
            self.in_progress.set('0%')

        # calendar settings
        prop = {op: CONFIG.get('Calendar', op) for op in CONFIG.options('Calendar')}
        prop['font'] = "Liberation\ Sans 9"
        prop.update(selectforeground='white', selectbackground=active_bg)
        locale = CONFIG.get('General', 'locale')

        # --- *--- start date
        self.start_date = self.event['Start']
        self.start_entry = DateEntry(frame_start, locale=locale, width=10,
                                     justify='center',
                                     year=self.start_date.year,
                                     month=self.start_date.month,
                                     day=self.start_date.day, **prop)

        self.start_hour = Combobox(frame_start, width=3, justify='center',
                                   state='readonly', exportselection=False,
                                   values=['%02d' % i for i in range(24)])
        self.start_hour.set('%02d' % self.start_date.hour)
        self.start_min = Combobox(frame_start, width=3, justify='center',
                                  state='readonly', exportselection=False,
                                  values=['%02d' % i for i in range(0, 60, 5)])
        self.start_min.set('%02d' % self.start_date.minute)
        self.start_entry.pack(side='left', padx=(0, 18))
        self.start_hour.pack(side='left', padx=(4, 0))
        Label(frame_start, text=':').pack(side='left')
        self.start_min.pack(side='left', padx=(0, 4))
        Checkbutton(frame_start, text=_("whole day"), variable=self._whole_day,
                    command=self._toggle_whole_day).pack(side='left', padx=4)

        # --- *--- end date
        self.end_date = self.event['End']
        self.end_entry = DateEntry(frame_end, justify='center',
                                   locale=locale, width=10,
                                   year=self.end_date.year,
                                   month=self.end_date.month,
                                   day=self.end_date.day, **prop)

        self.end_hour = Combobox(frame_end, width=3, justify='center',
                                 state='readonly', exportselection=False,
                                 values=['%02d' % i for i in range(24)])
        self.end_hour.set('%02d' % self.end_date.hour)
        self.end_min = Combobox(frame_end, width=3, justify='center',
                                state='readonly', exportselection=False,
                                values=['%02d' % i for i in range(0, 60, 5)])
        self.end_min.set('%02d' % self.end_date.minute)
        self.end_entry.pack(side='left', padx=(0, 18))

        self.end_hour.pack(side='left', padx=(4, 0))
        Label(frame_end, text=':').pack(side='left')
        self.end_min.pack(side='left', padx=(0, 4))

        for date in self.event['Reminders'].values():
            self.add_reminder(date)

        self._toggle_whole_day()

        # --- repetition settings
        frame_rep = Frame(notebook)
        notebook.add(frame_rep, text=_('Repetition'), padding=4, sticky='eswn')
        frame_rep.columnconfigure(0, weight=1)
        frame_rep.columnconfigure(1, weight=1)
        frame_rep.rowconfigure(1, weight=1)
        self._repeat = BooleanVar(self, bool(self.event['Repeat']))
        repeat = {'Frequency': 'year', 'Limit': 'always', 'NbTimes': 1,
                  'EndDate': (datetime.now() + timedelta(days=1)).date(),
                  'WeekDays': [self.start_date.isocalendar()[2] - 1]}
        repeat.update(self.event['Repeat'])

        self._repeat_freq = StringVar(self, repeat['Frequency'])
        Checkbutton(frame_rep, text=_('Repeat event'), variable=self._repeat,
                    command=self._toggle_rep).grid(row=0, column=0, columnspan=2,
                                                   padx=4, pady=6, sticky='w')
        # --- *--- Frequency
        frame_freq = LabelFrame(frame_rep, text=_('Frequency'))
        frame_freq.grid(row=1, column=0, sticky='eswn', padx=(0, 3))
        self._lfreq = Label(frame_freq, text=_('Every:'))
        self._lfreq.grid(row=0, column=0, padx=4, pady=2, sticky='e')

        self._freqs = []
        for i, val in enumerate(['Year', 'Month', 'Week']):
            r = Radiobutton(frame_freq, text=_(val), variable=self._repeat_freq,
                            value=val.lower(), command=self._toggle_wd)
            r.grid(row=i, column=1, padx=4, pady=2, sticky='nw')
            self._freqs.append(r)

        frame_days = Frame(frame_freq)
        frame_days.grid(row=2, column=2, padx=4, pady=2, sticky='nw')
        self._week_days = []
        cal = get_calendar(locale)
        days = cal.formatweekheader(10).split()
        for day in days:
            ch = Checkbutton(frame_days, text=day)
            ch.pack(anchor='w')
            self._week_days.append(ch)

        for d in repeat['WeekDays']:
            self._week_days[int(d)].state(('selected',))

        # --- *--- Limit
        frame_lim = LabelFrame(frame_rep, text=_('Limit'))
        frame_lim.grid(row=1, column=1, sticky='eswn', padx=(3, 0))
        self._repeat_lim = StringVar(self, repeat['Limit'])

        # always
        r1 = Radiobutton(frame_lim, text=_('Always'), value='always',
                         variable=self._repeat_lim, command=self._toggle_lim)
        r1.grid(row=0, column=0, sticky='w')
        # until
        r2 = Radiobutton(frame_lim, text=_('Until'), value='until',
                         variable=self._repeat_lim, command=self._toggle_lim)
        r2.grid(row=1, column=0, sticky='w')
        until_date = repeat['EndDate']
        self.until_entry = DateEntry(frame_lim, width=10, justify='center',
                                     locale=locale,
                                     year=until_date.year,
                                     month=until_date.month,
                                     day=until_date.day, **prop)

        self.until_entry.grid(row=1, column=1, columnspan=2, sticky='w',
                              padx=(4, 10), pady=2)

        # after
        r3 = Radiobutton(frame_lim, text=_('After'), value='after',
                         variable=self._repeat_lim, command=self._toggle_lim)
        r3.grid(row=2, column=0, sticky='w')
        frame_after = Frame(frame_lim, style='txt.TFrame', relief='sunken', border=1)
        self.s_after = Spinbox(frame_after, from_=0, to=100, width=3, justify='center',
                               relief='flat', highlightthickness=0, validate='key',
                               validatecommand=(self._only_nb, '%P'),
                               disabledbackground='white')
        self.s_after.pack()
        self.s_after.delete(0, 'end')
        self.s_after.insert(0, str(repeat['NbTimes']))
        frame_after.grid(row=2, column=1, padx=4, pady=2, sticky='w')
        self._llim = Label(frame_lim, text=_('times'))
        self._llim.grid(row=2, column=2, padx=0, pady=2, sticky='w')

        self._rb_lim = [r1, r2, r3]

        self._toggle_rep()
        self._change_label()

        # --- bindings
        self.bind('<Configure>')
        self.task_progress.bind('<<ComboboxSelected>>', self._toggle_in_progress)
        self.start_entry.bind('<<DateEntrySelected>>', self._select_start)
        self.end_entry.bind('<<DateEntrySelected>>', self._select_end)
        self.start_hour.bind("<<ComboboxSelected>>", self._select_start_hour)
        self.start_min.bind("<<ComboboxSelected>>", self._select_start_min)
        self.end_min.bind("<<ComboboxSelected>>", self._select_end_time)
        self.end_hour.bind("<<ComboboxSelected>>", self._select_end_time)
        self.bind_class("TCombobox", "<<ComboboxSelected>>", self.__clear_selection, add=True)

        self.wait_visibility(self)
        self.grab_set()
        self.summary.focus_set()

    def _toggle_lim(self, val=True):
        if val:
            val = self._repeat_lim.get()

        if val == 'until':
            self.s_after.configure(state='disabled')
            self._llim.state(('disabled',))
            self.until_entry.state(('!disabled',))
        elif val == 'after':
            self._llim.state(('!disabled',))
            self.s_after.configure(state='normal')
            self.until_entry.state(('disabled',))
        else:
            self.s_after.configure(state='disabled')
            self._llim.state(('disabled',))
            self.until_entry.state(('disabled',))

    def _toggle_rep(self):
        rep = self._repeat.get()
        state = state = '!' * int(rep) + "disabled"
        for r in self._freqs:
            r.state((state,))
        for r in self._rb_lim:
            r.state((state,))
        self._lfreq.state((state,))
        self._toggle_wd(rep)
        self._toggle_lim(rep)

    def _toggle_wd(self, val=True):
        if val:
            val = self._repeat_freq.get()
        state = '!' * int(val == 'week') + "disabled"
        for ch in self._week_days:
            ch.state((state,))

    def _toggle_whole_day(self):
        if self._whole_day.get():
            self.start_min.set('00')
            self.start_hour.set('00')
            self.end_min.set('59')
            self.end_hour.set('23')
            self.start_min.state(("disabled",))
            self.start_hour.state(("disabled",))
            self.end_min.state(("disabled",))
            self.end_hour.state(("disabled",))
        else:
            self.start_min.state(("!disabled",))
            self.start_hour.state(("!disabled",))
            self.end_min.state(("!disabled",))
            self.end_hour.state(("!disabled",))

    def _toggle_in_progress(self, event=None):
        if self.task_progress.get() == _('In Progress'):
            self.in_progress.state(('!disabled',))
        else:
            if self.task_progress.get() == _('Completed'):
                self.in_progress.set('100%')
            self.in_progress.state(('disabled',))

    def _change_label(self):
        if self._task.get():
            self.task_progress.state(('!disabled',))
            self._toggle_in_progress()
            self._end_label.configure(text=_('Deadline'))
        else:
            self.task_progress.state(('disabled',))
            self.in_progress.state(('disabled',))
            self._end_label.configure(text=_('End'))

    def _on_move(self, event):
        self.start_cal.withdraw()
        self.end_cal.withdraw()
        self.until_cal.withdraw()

    @staticmethod
    def __clear_selection(event):
        combo = event.widget
        combo.selection_clear()

    def _select_start(self, event=None):
        dt = self.start_entry.get_date() - self.start_date
        self.end_date = self.end_date + dt
        self.end_entry.set_date(self.end_date)
        self.start_date = self.start_entry.get_date()

    def _select_end(self, event=None):
        self.end_date = self.end_entry.get_date()
        start = self.start_entry.get_date()
        if start >= self.end_date:
            self.start_date = self.end_date
            self.start_entry.set_date(self.end_date)
            start_time = time(int(self.start_hour.get()), int(self.start_min.get()))
            end_time = time(int(self.start_hour.get()), int(self.end_min.get()))
            if start_time > end_time:
                self.start_hour.set(self.end_hour.get())
                self.start_min.set(self.end_min.get())

    def _select_start_hour(self, event):
        h = int(self.start_hour.get())
        self.end_hour.set('%02d' % ((h + 1) % 24))

    def _select_start_min(self, event):
        m = int(self.start_min.get())
        self.end_min.set('%02d' % m)

    def _select_end_time(self, event):
        if self.start_entry.get() == self.end_entry.get():
            start_time = time(int(self.start_hour.get()), int(self.start_min.get()))
            end_time = time(int(self.end_hour.get()), int(self.end_min.get()))
            if start_time > end_time:
                self.start_hour.set(self.end_hour.get())
                self.start_min.set(self.end_min.get())

    def add_reminder(self, date=None):

        def remove():
            self.alarms.remove((when, what))
            rem.destroy()

        rem = Frame(self.frame_alarms)
        frame_when = Frame(rem, style='txt.TFrame', relief='sunken', border=1)
        when = Spinbox(frame_when, from_=0, to=59, width=3, justify='center',
                       relief='flat', highlightthickness=0, validate='key',
                       validatecommand=(self._only_nb, '%P'))
        when.pack()
        when.delete(0, 'end')
        what = Combobox(rem, width=8, state='readonly',
                        values=(_('minutes'), _('hours'), _('days')))

        if date:
            hour = int(self.start_hour.get())
            minute = int(self.start_min.get())
            dt = self.start_entry.get_date().replace(hour=hour, minute=minute) - date
            if dt.days > 0:
                when.insert(0, str(dt.days))
                what.set(_('days'))
            else:
                h, m, s = str(dt).split(':')
                if h != "0":
                    when.insert(0, h)
                    what.set(_('hours'))
                else:
                    while m[0] is '0':
                        m = m[1:]
                    if not m:
                        m = '0'
                    when.insert(0, m)
                    what.set(_('minutes'))
        else:
            when.insert(0, '15')
            what.set(_('minutes'))

        self.alarms.append((when, what))

        Label(rem, text=_('Reminder:')).pack(side='left', padx=4, pady=4)
        frame_when.pack(side='left', pady=4, padx=4)
        what.pack(side='left', pady=4, padx=4)
        Button(rem, image=self.img_moins, padding=0,
               command=remove).pack(side='left', padx=4, pady=4)
        rem.pack()

    def ok(self):
        self.event['Summary'] = self.summary.get()
        self.event['Place'] = self.place.get()
        self.event['Start'] = "%s %s:%s" % (self.start_entry.get(),
                                            self.start_hour.get(),
                                            self.start_min.get())
        self.event['End'] = "%s %s:%s" % (self.end_entry.get(),
                                          self.end_hour.get(),
                                          self.end_min.get())
        self.event['Description'] = self.desc.get('1.0', 'end')
        self.event['Category'] = self.category.get()
        if not self._task.get():
            self.event['Task'] = False
        else:
            prog = self.task_progress.get()
            if prog == _('In Progress'):
                self.event['Task'] = self.in_progress.get()
            else:
                self.event['Task'] = TASK_REV_TRANSLATION[prog]

        self.event["WholeDay"] = self._whole_day.get()

        if not self._repeat.get():
            self.event['Repeat'] = {}
        else:
            days = []
            for i in range(7):
                if "selected" in self._week_days[i].state():
                    days.append(i)
            repeat = {'Frequency': self._repeat_freq.get(),
                      'Limit': self._repeat_lim.get(),
                      'NbTimes': int(self.s_after.get()),
                      'EndDate': datetime.strptime(self.until_entry.get(), '%x').date(),
                      'WeekDays': days}
            self.event['Repeat'] = repeat

        self.event.reminder_remove_all()
        for when, what in self.alarms:
            dt = int(when.get())
            unit = FREQ_REV_TRANSLATION[what.get()]
            date = self.event['Start'] - timedelta(**{unit: dt})
            self.event.reminder_add(date)

        if self._new:
            self.master.event_add(self.event)
        else:
            self.master.event_configure(self.event.iid)
        self.destroy()

    def cancel(self):
        if not self._new:
            self.master.widgets['Calendar'].add_event(self.event)
        self.destroy()
