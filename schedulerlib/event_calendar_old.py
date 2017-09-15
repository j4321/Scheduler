#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


EventCalendar: Calendar with the possibility to display events.
"""

from tkinter import Menu
from datetime import datetime
from schedulerlib.constants import HOLIDAYS, CATEGORIES
from schedulerlib.ttkcalendar import Calendar
from schedulerlib.tooltip import TooltipWrapper


class EventCalendar(Calendar):
    """ Calendar widget that can display events. """
    def __init__(self, master=None, **kw):
        """
            Create an EventCalendar.

            KEYWORD OPTIONS COMMON WITH CALENDAR

                cursor, font, year, month, day, locale,
                background, foreground, bordercolor, othermonthforeground,
                selectbackground, selectforeground,
                normalbackground, normalforeground,
                weekendbackground, weekendforeground,
                headersbackground, headersforeground

            WIDGET-SPECIFIC OPTIONS

                tooltipforeground, tooltipbackground, tooltipalpha

            selectmode is set to 'none' and cannot be changed

        """
        tp_fg = kw.pop('tooltipforeground', 'white')
        tp_bg = kw.pop('tooltipbackground', 'black')
        tp_alpha = kw.pop('tooltipalpha', 0.8)
        kw['selectmode'] = 'none'

        self._events = {}
        self._repeated_events = {'year': {}, 'month': {},
                                 'week':{i:[] for i in range(7)}}
        self._events_tooltips = [[None for i in range(7)] for j in range(6)]
        self._holidays = {}

        Calendar.__init__(self, master, class_='EventCalendar', **kw)

        self._properties['tooltipbackground'] = tp_bg
        self._properties['tooltipforeground'] = tp_fg
        self._properties['tooltipalpha'] = tp_alpha

        for cat, (fg, bg) in CATEGORIES.items():
            style = '%s.ev_%s.TLabel' % (self._style_prefixe, cat)
            self.style.configure(style, background=bg, foreground=fg)
        self._menu = Menu(self, tearoff=False)

        for i, week in enumerate(self._calendar):
            for j, day in enumerate(week):
                day.bind('<Double-1>', lambda e, w=i: self._on_dbclick(e, w))
                day.bind('<3>', lambda e, w=i: self._post_menu(e, w))

    def __setitem__(self, item, value):
        if item == 'tooltipbackground':
            self._properties[item] = value
            for line in self._events_tooltips:
                for tp in line:
                    tp.configure(background=value)
        elif item == 'tooltipforeground':
            self._properties[item] = value
            for line in self._events_tooltips:
                for tp in line:
                    tp.configure(foreground=value)
        elif item == 'tooltipalpha':
            self._properties[item] = value
            for line in self._events_tooltips:
                for tp in line:
                    tp.configure(alpha=value)
        elif item == 'selectmode':
            raise AttributeError('This attribute cannot be modified.')
        else:
            Calendar.__setitem__(self, item, value)

    def _get_cal(self, year, month):
        cal = self._cal.monthdatescalendar(year, month)
        m = month + 1
        y = year
        if m == 13:
            m = 1
            y += 1
        if len(cal) < 6:
            cal.append(self._cal.monthdatescalendar(y, m)[1])
        return cal

    def _display_calendar(self):
        Calendar._display_calendar(self)
        year, month = self._date.year, self._date.month

        # --- clear tooltips
        for i in range(6):
            for j in range(7):
                tp = self._events_tooltips[i][j]
                if tp is not None:
                    tp.destroy()
                    self._events_tooltips[i][j] = None

        # --- display holidays
        if year in self._holidays:
            if month in self._holidays[year]:
                hd = self._holidays[year][month]
                for day in hd:
                    date = self.date(year, month, day)
                    _, w, d = date.isocalendar()
                    w -= self._date.isocalendar()[1]
                    w %= 52
                    label = self._calendar[w][d - 1]
                    label.configure(style=self._style_prefixe + '.we.TLabel')

        # --- display events
        # --- *-- one time events
        if year in self._events:
            if month in self._events[year]:
                evts = self._events[year][month]
                for day in evts:
                    date = self.date(year, month, day)
                    txt = '\n'.join([k[0] for k in evts[day]])
                    cat = evts[day][-1][-1]
                    self._show_event(date, txt, cat)
        # --- *-- yearly events
        if month in self._repeated_events['year']:
            evts = self._repeated_events['year'][month]
            for day, vals in evts.items():
                date = self.date(year, month, day)
                for desc, iid, start, end, cat in vals:
                    if date >= start and (end is None or date <= end) :
                        self._show_event(date, desc, cat)
        # --- *-- monthly events
        for day, vals in self._repeated_events['month'].items():
            for desc, iid, start, end, cat in vals:
                # previous month
                if day > 22:
                    m = self._date.month - 1
                    y = self._date.year
                    if m == -1:
                        m = 12
                        y -= 1
                    try:
                        ev_date = self.date(y, m, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._show_event(ev_date, desc, cat)
                    except ValueError:
                        pass # month has no day 'day'
                # current month
                try:
                    ev_date = self.date(self._date.year, self._date.month, day)
                    if (end is None or ev_date <= end) and (ev_date >= start):
                        self._show_event(ev_date, desc, cat)
                except ValueError:
                    pass # month has no day 'day'
                # next month
                if day < 15:
                    try:
                        m = self._date.month + 1
                        y = self._date.year
                        if m == 13:
                            m = 1
                            y += 1
                        ev_date = self.date(y, m, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._show_event(ev_date, desc, cat)
                    except ValueError:
                        pass # month has no day 'day'
        # --- *-- weekly events
        cal = self._get_cal(self._date.year, self._date.month)
        for d, vals in self._repeated_events['week'].items():
            for desc, iid, start, end, cat in vals:
                if start < cal[0][0]:
                    w_min = 0
                    d_min = 0
                elif start > cal[-1][-1]:
                    w_min = 6
                    d_min = 7
                else:
                    _, w_min, d_min = start.isocalendar()
                    w_min -= self._date.isocalendar()[1]
                    w_min %= 52
                    d_min -= 1

                if end is None or end > cal[-1][-1]:
                    w_max = 6
                    d_max = 7
                elif end < cal[0][0]:
                    w_max = -1
                    d_max = -1
                else:
                    _, w_max, d_max = end.isocalendar()
                    w_max -= self._date.isocalendar()[1]
                    w_max %= 52

                for w in range(w_min + 1, w_max):
                    self._add_to_tooltip(w, d, desc, cat)
                if w_min < w_max:
                    if d >= d_min:
                        self._add_to_tooltip(w_min, d, desc, cat)
                if w_max < 6:
                    if d < d_max:
                        self._add_to_tooltip(w_max, d, desc, cat)

    def _add_to_tooltip(self, week_nb, day, txt, cat):
        tp = self._events_tooltips[week_nb][day]
        label = self._calendar[week_nb][day]
        label.configure(style= '%s.ev_%s.TLabel' % (self._style_prefixe, cat))
        if tp is None:
            prop = {'background': self._properties['tooltipbackground'],
                    'foreground': self._properties['tooltipforeground'],
                    'alpha': self._properties['tooltipalpha'],
                    'text': txt, 'font': self._font}
            self._events_tooltips[week_nb][day] = TooltipWrapper(label, **prop)
        else:
            tp.configure(text='\n'.join([tp.cget('text'), txt]))

    def _remove_from_tooltip(self, date, txt):
        year, month, day = date.year, date.month, date.day
        if self._date.year == year:
            _, week_nb, d = date.isocalendar()
            d -= 1
            week_nb -= self._date.isocalendar()[1]
            week_nb %= 52
            if week_nb < 6:
                tp = self._events_tooltips[week_nb][d]
                if tp is not None:
                    text = tp.cget('text').split('\n')
                    try:
                        text.remove(txt)
                    except ValueError:
                        return
                    if text:
                        tp.configure(text='\n'.join(text))
                    else:
                        tp.destroy()
                        self._events_tooltips[week_nb][d] = None
                        label = self._calendar[week_nb][d]
                        if type(date) == datetime:
                            date = date.date()
                        if date == self._sel_date:
                            label.configure(style=self._style_prefixe + ".sel.TLabel")
                        elif (year in self._holidays and
                            month in self._holidays[year] and
                            day in self._holidays[year][month]):
                            label.configure(style=self._style_prefixe + ".we.TLabel")
                        else:
                            if month == self._date.month:
                                if d < 6:
                                    label.configure(style=self._style_prefixe + ".normal.TLabel")
                                else:
                                    label.configure(style=self._style_prefixe + ".we.TLabel")
                            else:
                                if d < 6:
                                    label.configure(style=self._style_prefixe + ".normal_om.TLabel")
                                else:
                                    label.configure(style=self._style_prefixe + ".we_om.TLabel")

    def _show_event(self, date, txt, cat):
        if date.year == self._date.year:
            _, w, d = date.isocalendar()
            w -= self._date.isocalendar()[1]
            w %= 52
            if w < 6:
                self._add_to_tooltip(w, d - 1, txt, cat)

    def _add_event(self, date, desc, iid, repeat, cat):
        year, month, day = date.year, date.month, date.day
        if not repeat:
            if not year in self._events:
                self._events[year] = {}
            if not month in self._events[year]:
                self._events[year][month] = {}
            if not day in self._events[year][month]:
                self._events[year][month][day] = []
            self._events[year][month][day].append((desc, iid, cat))
            self._show_event(date, desc, cat)
        else:
            start = date.date()
            freq = repeat['Frequency']
            if repeat['Limit'] == 'until':
                end = repeat['EndDate']
            elif repeat['Limit'] == 'after':
                nb = repeat['NbTimes'] - 1  # date is the first time
                if freq == 'year':
                    end = date.replace(year=date.year + nb)
                elif freq == 'month':
                    m = date.month + nb
                    month = m % 12
                    year = date.year + m//12
                    end = date.replace(year=year, month=month)
                else:
                    start_day = date.isocalendar()[2] - 1
                    week_days = [(x - start_day) % 7 for x in repeat['WeekDays']]

                    nb_per_week = len(repeat['WeekDays'])
                    nb_week = nb//nb_per_week
                    rem = nb % nb_per_week
                    end = date + self.timedelta(days=(7*nb_week + week_days[rem] + 1))
                end = end.date()
            else:
                end = None
            if freq == 'year':
                if not month in self._repeated_events[freq]:
                    self._repeated_events[freq][month] = {}
                if not day in self._repeated_events[freq][month]:
                    self._repeated_events[freq][month][day] = []
                self._repeated_events[freq][month][day].append((desc, iid, start, end, cat))
                ev_date = self.date(self._date.year, month, day)
                if (end is None or ev_date <= end) and (ev_date >= start):
                    self._show_event(ev_date, desc, cat)

            elif freq == 'month':
                if not day in self._repeated_events[freq]:
                    self._repeated_events[freq][day] = []
                self._repeated_events[freq][day].append((desc, iid, start, end, cat))
                # previous month
                if day > 22:
                    m = self._date.month - 1
                    y = self._date.year
                    if m == -1:
                        m = 12
                        y -= 1
                    try:
                        ev_date = self.date(y, m, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._show_event(ev_date, desc, cat)
                    except ValueError:
                        pass # month has no day 'day'
                # current month
                try:
                    ev_date = self.date(self._date.year, self._date.month, day)
                    if (end is None or ev_date <= end) and (ev_date >= start):
                        self._show_event(ev_date, desc, cat)
                except ValueError:
                    pass # month has no day 'day'
                # next month
                if day < 15:
                    try:
                        m = self._date.month + 1
                        y = self._date.year
                        if m == 13:
                            m = 1
                            y += 1
                        ev_date = self.date(y, m, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._show_event(ev_date, desc, cat)
                    except ValueError:
                        pass # month has no day 'day'

            elif freq == 'week':
                cal = self._get_cal(self._date.year, self._date.month)
                if start < cal[0][0]:
                    w_min = 0
                    d_min = 0
                elif start > cal[-1][-1]:
                    w_min = 6
                    d_min = 7
                else:
                    _, w_min, d_min = start.isocalendar()
                    w_min -= self._date.isocalendar()[1]
                    w_min %= 52
                    d_min -= 1

                if end is None or end > cal[-1][-1]:
                    w_max = 6
                    d_max = 7
                elif end < cal[0][0]:
                    w_max = 0
                    d_max = 0
                else:
                    _, w_max, d_max = end.isocalendar()
                    w_max -= self._date.isocalendar()[1]
                    w_max %= 52
                for d in repeat['WeekDays']:
                    self._repeated_events[freq][d].append((desc, iid, start, end, cat))
                    for w in range(w_min + 1, w_max):
                        self._add_to_tooltip(w, d, desc, cat)
                if w_min < w_max:
                    for d in repeat['WeekDays']:
                        if d >= d_min:
                            self._add_to_tooltip(w_min, d, desc, cat)
                if w_max < 6:
                    for d in repeat['WeekDays']:
                        if d < d_max:
                            self._add_to_tooltip(w_max, d, desc, cat)

    def _remove_event(self, date, desc, iid, repeat, cat):
        year, month, day = date.year, date.month, date.day
        if not repeat:
            if not year in self._events:
                raise ValueError('Event not in calendar.')
            elif not month in self._events[year]:
                raise ValueError('Event not in calendar.')
            elif not day in self._events[year][month]:
                raise ValueError('Event not in calendar.')
            elif not (desc, iid, cat) in self._events[year][month][day]:
                raise ValueError('Event not in calendar.')
            else:
                self._events[year][month][day].remove((desc, iid, cat))
                if not self._events[year][month][day]:
                    del(self._events[year][month][day])
                self._remove_from_tooltip(date, desc)
        else:
            start = date.date()
            freq = repeat['Frequency']
            if repeat['Limit'] == 'until':
                end = repeat['EndDate']
            elif repeat['Limit'] == 'after':
                nb = repeat['NbTimes'] - 1  # date is the first time
                if freq == 'year':
                    end = date.replace(year=date.year + nb)
                elif freq == 'month':
                    m = date.month + nb
                    month = m % 12
                    year = date.year + m//12
                    end = date.replace(year=year, month=month)
                else:
                    start_day = date.isocalendar()[2] - 1
                    week_days = [(x - start_day) % 7 for x in repeat['WeekDays']]

                    nb_per_week = len(repeat['WeekDays'])
                    nb_week = nb//nb_per_week
                    rem = nb % nb_per_week
                    end = date + self.timedelta(days=(7*nb_week + week_days[rem] + 1))
                end = end.date()
            else:
                end = None
            if freq == 'year':
                if not month in self._repeated_events[freq]:
                    raise ValueError('Event not in calendar.')
                elif not day in self._repeated_events[freq][month]:
                    raise ValueError('Event not in calendar.')
                self._repeated_events[freq][month][day].remove((desc, iid, start, end, cat))
                if not self._repeated_events[freq][month][day]:
                    del(self._repeated_events[freq][month][day])
                ev_date = self.date(self._date.year, month, day)
                if (end is None or ev_date <= end) and (ev_date >= start):
                    self._remove_from_tooltip(ev_date, desc)

            elif freq == 'month':
                if not day in self._repeated_events[freq]:
                    raise ValueError('Event not in calendar.')
                self._repeated_events[freq][day].remove((desc, iid, start, end, cat))
                if not self._repeated_events[freq][day]:
                    del( self._repeated_events[freq][day])
                # previous month
                if day > 22:
                    m = self._date.month - 1
                    y = self._date.year
                    if m == -1:
                        m = 12
                        y -= 1
                    try:
                        ev_date = self.date(y, m, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._remove_from_tooltip(ev_date, desc)
                    except ValueError:
                        pass # month has no day 'day'
                # current month
                try:
                    ev_date = self.date(self._date.year, self._date.month, day)
                    if (end is None or ev_date <= end) and (ev_date >= start):
                        self._remove_from_tooltip(ev_date, desc)
                except ValueError:
                    pass # month has no day 'day'
                # next month
                if day < 15:
                    try:
                        m = self._date.month + 1
                        y = self._date.year
                        if m == 13:
                            m = 1
                            y += 1
                        ev_date = self.date(y, m, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._remove_from_tooltip(ev_date, desc)
                    except ValueError:
                        pass # month has no day 'day'

            elif freq == 'week':
                cal = self._get_cal(self._date.year, self._date.month)
                for d in repeat['WeekDays']:
                    try:
                        self._repeated_events[freq][d].remove((desc, iid, start, end, cat))
                    except ValueError:
                        raise ValueError('Event not in calendar.')
                    for w in range(6):
                        self._remove_from_tooltip(cal[w][d], desc)

    def _get_date(self, week_row, day):
        year, month = self._date.year, self._date.month
        now = datetime.now() + self.timedelta(minutes=5)
        now = now.replace(minute=(now.minute//5)*5)
        if week_row == 0 and day > 7:
            # prev month
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1

        elif week_row in [4, 5] and day < 15:
            # next month
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        return datetime(year, month, day, now.hour, now.minute)

    # --- bindings
    def _on_dbclick(self, event, w):
        day = int(event.widget.cget('text'))
        date = self._get_date(w, day)
        self.master.master.add(date)

    def _post_menu(self, event, w):
        self._menu.delete(0, 'end')
        day = int(event.widget.cget('text'))
        date = self._get_date(w, day)
        date2 = date.date()

        year, month = date.year, date.month
        if (year in self._events and
            month in self._events[year] and
            day in self._events[year][month]):
            evts = self._events[year][month][day]
        else:
            evts = []
        if (month in self._repeated_events['year'] and
            day in self._repeated_events['year'][month]):
            for desc, iid, start, end, cat in self._repeated_events['year'][month][day]:
                if start <= date2 and (end is None or end >= date2):
                    evts.append((desc, iid))
        if day in self._repeated_events['month']:
            for desc, iid, start, end, cat in self._repeated_events['month'][day]:
                if start <= date2 and (end is None or end >= date2):
                    evts.append((desc, iid))
        d = date.isocalendar()[2] - 1
        if d in self._repeated_events['week']:
            for desc, iid, start, end, cat in self._repeated_events['week'][d]:
                if start <= date2 and (end is None or end >= date2):
                    evts.append((desc, iid))

        self._menu.add_command(label='New Event',
                               command=lambda: self.master.master.add(date))
        if evts:
            self._menu.add_separator()
            self._menu.add_separator()
            index_edit = 2
            for vals in evts:
                desc, iid = vals[0], vals[1]
                self._menu.insert_command(index_edit,
                                          label="Edit %s" % desc,
                                          command=lambda i=iid: self.master.master.edit(i))
                index_edit += 1
                self._menu.add_command(label="Delete %s" % desc,
                                       command=lambda i=iid: self.master.master.delete(i))
        else:
            self._menu.add_separator()
            if date.strftime('%x') in HOLIDAYS:
                self._menu.add_command(label='Remove Holiday',
                                       command=lambda: self.remove_holiday(date.date()))
            else:
                self._menu.add_command(label='Set Holiday',
                                       command=lambda: self.add_holiday(date.date()))

        self._menu.tk_popup(event.x_root, event.y_root)

    # --- public methods
    def add_holiday(self, date):
        year, month, day = date.year, date.month, date.day
        HOLIDAYS.add(date.strftime('%x'))
        if not year in self._holidays:
            self._holidays[year] = {}
        if not month in self._holidays[year]:
            self._holidays[year][month] = []
        self._holidays[year][month].append(day)
        if year == self._date.year:
            _, w, d = date.isocalendar()
            w -= self._date.isocalendar()[1]
            w %= 52
            if 0 <= w and w < 6:
                style = self._calendar[w][d - 1].cget('style')
                we_style = self._style_prefixe + ".we.TLabel"
                we_om_style = self._style_prefixe + ".we_om.TLabel"
                normal_style = self._style_prefixe + ".normal.TLabel"
                normal_om_style = self._style_prefixe + ".normal_om.TLabel"
                if style == normal_style:
                    self._calendar[w][d - 1].configure(style=we_style)
                elif style == normal_om_style:
                    self._calendar[w][d - 1].configure(style=we_om_style)

    def remove_holiday(self, date):
        year, month, day = date.year, date.month, date.day
        try:
            HOLIDAYS.remove(date.strftime('%x'))
            self._holidays[year][month].remove(day)
            if year == self._date.year:
                _, w, d = date.isocalendar()
                w -= self._date.isocalendar()[1]
                w %= 52
                if 0 <= w and w < 6:
                    style = self._calendar[w][d - 1].cget('style')
                    we_style = self._style_prefixe + ".we.TLabel"
                    we_om_style = self._style_prefixe + ".we_om.TLabel"
                    normal_style = self._style_prefixe + ".normal.TLabel"
                    normal_om_style = self._style_prefixe + ".normal_om.TLabel"
                    if style == we_style:
                        self._calendar[w][d - 1].configure(style=normal_style)
                    elif style == we_om_style:
                        self._calendar[w][d - 1].configure(style=normal_om_style)
        except ValueError:
            raise ValueError('%s is not a holiday.' % date.strftime('%x'))

    def add_event(self, event):
        start = event['Start']
        end = event['End']
        if not event["WholeDay"]:
            deb = start.strftime('%H:%M')
            fin = end.strftime('%H:%M')
            desc = '➢ %s - %s %s' % (deb, fin, event['Summary'])
        else:
            desc = '➢ %s' % event['Summary']
        repeat = event['Repeat']
        dt = end - start
        for d in range(dt.days + 1):
            self._add_event(start + self.timedelta(days=d),
                            desc, event.iid, repeat, event['Category'])

    def remove_event(self, event):
        start = event['Start']
        end = event['End']
        if not event["WholeDay"]:
            deb = start.strftime('%H:%M')
            fin = end.strftime('%H:%M')
            desc = '➢ %s - %s %s' % (deb, fin, event['Summary'])
        else:
            desc = '➢ %s' % event['Summary']
        repeat = event['Repeat']
        dt = end - start
        for d in range(dt.days + 1):
            self._remove_event(start + self.timedelta(days=d),
                               desc, event.iid, repeat, event['Category'])

