#!/usr/bin/env python3
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


EventCalendar: Calendar with the possibility to display events.
"""
from tkinter import Menu
from datetime import datetime
import logging

from tkcalendar import Calendar

from schedulerlib.constants import HOLIDAYS, CONFIG, format_date, format_time
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
        self._weekly_events = {i: [] for i in range(7)}
        self._events_tooltips = [[None for i in range(7)] for j in range(6)]

        Calendar.__init__(self, master, class_='EventCalendar', **kw)

        self._properties['tooltipbackground'] = tp_bg
        self._properties['tooltipforeground'] = tp_fg
        self._properties['tooltipalpha'] = tp_alpha

        self.menu = Menu(self)

        for i, week in enumerate(self._calendar):
            for j, day in enumerate(week):
                day.bind('<Double-1>', lambda e, w=i: self._on_dbclick(e, w))
                day.bind('<3>', lambda e, w=i: self._post_menu(e, w))

    def update_style(self):
        cats = {cat: CONFIG.get('Categories', cat).split(', ') for cat in CONFIG.options('Categories')}
        for cat, (fg, bg) in cats.items():
            style = 'ev_%s.%s.TLabel' % (cat, self._style_prefixe)
            self.style.configure(style, background=bg, foreground=fg)

    def __setitem__(self, item, value):
        if item == 'tooltipbackground':
            self._properties[item] = value
            for line in self._events_tooltips:
                for tp in line:
                    if tp is not None:
                        tp.configure(background=value)
        elif item == 'tooltipforeground':
            self._properties[item] = value
            for line in self._events_tooltips:
                for tp in line:
                    if tp is not None:
                        tp.configure(foreground=value)
        elif item == 'tooltipalpha':
            self._properties[item] = value
            for line in self._events_tooltips:
                for tp in line:
                    if tp is not None:
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

    def update_sel(self):
        """Update current day"""
        logging.info('Update current day to %s' % self.date.today())
        self._sel_date = self.date.today()
        if self._sel_date.month != self._date.month:
            self._date = self._sel_date.replace(day=1)
            self._display_calendar()
        self._display_selection()

    def _display_calendar(self):
        Calendar._display_calendar(self)

        year, month = self._date.year, self._date.month
        cal = self._get_cal(year, month)

        # --- clear tooltips
        for i in range(6):
            for j in range(7):
                tp = self._events_tooltips[i][j]
                if tp is not None:
                    tp.destroy()
                    self._events_tooltips[i][j] = None

        we_style = 'we.%s.TLabel' % self._style_prefixe
        we_om_style = 'we_om.%s.TLabel' % self._style_prefixe

        # --- display events and holidays
        for w in range(6):
            for d in range(7):
                day = cal[w][d]
                label = self._calendar[w][d]
                if not label.cget('text'):
                    continue
                date = day.strftime('%Y/%m/%d')
                # --- holidays
                if date in HOLIDAYS:
                    if month == day.month:
                        label.configure(style=we_style)
                    else:
                        label.configure(style=we_om_style)
                # --- one time event
                if date in self._events:
                    evts = self._events[date]
                    txt = '\n'.join([k[0] for k in evts])
                    cat = evts[-1][-1]
                    self._add_to_tooltip(w, d, txt, cat)
                # --- yearly event
                date = day.strftime('*/%m/%d')
                if date in self._events:
                    evts = self._events[date]
                    for desc, iid, start, end, cat in evts:
                        if day >= start and (end is None or day <= end):
                            self._add_to_tooltip(w, d, desc, cat)
                # --- monthly event
                date = day.strftime('*/*/%d')
                if date in self._events:
                    evts = self._events[date]
                    for desc, iid, start, end, cat in evts:
                        if day >= start and (end is None or day <= end):
                            self._add_to_tooltip(w, d, desc, cat)
                # --- weekly events
                evts = self._weekly_events[d]
                for desc, iid, start, end, cat in evts:
                    if day >= start and (end is None or day <= end):
                        self._add_to_tooltip(w, d, desc, cat)
        self._display_selection()

    def _add_to_tooltip(self, week_nb, day, txt, cat):
        tp = self._events_tooltips[week_nb][day]
        label = self._calendar[week_nb][day]
        label.configure(style='ev_%s.%s.TLabel' % (cat, self._style_prefixe))
        if tp is None:
            prop = {'background': self._properties['tooltipbackground'],
                    'foreground': self._properties['tooltipforeground'],
                    'alpha': self._properties['tooltipalpha'],
                    'text': txt, 'font': self._font}
            self._events_tooltips[week_nb][day] = TooltipWrapper(label, **prop)
        else:
            tp.configure(text='\n'.join([tp.cget('text'), txt]))

    def _remove_from_tooltip(self, date, txt):
        y1, y2 = date.year, self._date.year
        m1, m2 = date.month, self._date.month
        if y1 == y2 or (y1 - y2 == 1 and m1 == 1 and m2 == 12) or (y2 - y1 == 1 and m2 == 1 and m1 == 12):
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
                            label.configure(style='sel.%s.TLabel' % self._style_prefixe)
                        elif date.strftime('%Y/%m/%d') in HOLIDAYS:
                            if m1 == m2:
                                label.configure(style='we.%s.TLabel' % self._style_prefixe)
                            else:
                                label.configure(style='we_om.%s.TLabel' % self._style_prefixe)
                        else:
                            if m1 == m2:
                                if d < 5:
                                    label.configure(style='normal.%s.TLabel' % self._style_prefixe)
                                else:
                                    label.configure(style='we.%s.TLabel' % self._style_prefixe)
                            else:
                                if d < 5:
                                    label.configure(style='normal_om.%s.TLabel' % self._style_prefixe)
                                else:
                                    label.configure(style='we_om.%s.TLabel' % self._style_prefixe)

    def _show_event(self, date, txt, cat):
        y1, y2 = date.year, self._date.year
        m1, m2 = date.month, self._date.month
        if y1 == y2 or (y1 - y2 == 1 and m1 == 1 and m2 == 12) or (y2 - y1 == 1 and m2 == 1 and m1 == 12):
            _, w, d = date.isocalendar()
            w -= self._date.isocalendar()[1]
            w %= 52
            if w < 6:
                self._add_to_tooltip(w, d - 1, txt, cat)

    def _add_event(self, date, desc, iid, repeat, cat):
        year, month, day = date.year, date.month, date.day
        if not repeat:
            date2 = date.strftime('%Y/%m/%d')
            if date2 not in self._events:
                self._events[date2] = []
            self._events[date2].append((desc, iid, cat))
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
                    year = date.year + m // 12
                    end = date.replace(year=year, month=month)
                else:
                    start_day = date.isocalendar()[2] - 1
                    week_days = [(x - start_day) % 7 for x in repeat['WeekDays']]

                    nb_per_week = len(repeat['WeekDays'])
                    nb_week = nb // nb_per_week
                    rem = nb % nb_per_week
                    end = date + self.timedelta(days=(7 * nb_week + week_days[rem] + 1))
                end = end.date()
            else:
                end = None
            if freq == 'year':
                date2 = date.strftime('*/%m/%d')
                if date2 not in self._events:
                    self._events[date2] = []
                self._events[date2].append((desc, iid, start, end, cat))
                ev_date = self.date(self._date.year, month, day)
                if (end is None or ev_date <= end) and (ev_date >= start):
                    self._show_event(ev_date, desc, cat)

            elif freq == 'month':
                date2 = date.strftime('*/*/%d')
                if date2 not in self._events:
                    self._events[date2] = []
                self._events[date2].append((desc, iid, start, end, cat))
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
                        pass  # month has no day 'day'
                # current month
                try:
                    ev_date = self.date(self._date.year, self._date.month, day)
                    if (end is None or ev_date <= end) and (ev_date >= start):
                        self._show_event(ev_date, desc, cat)
                except ValueError:
                    pass  # month has no day 'day'
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
                        pass  # month has no day 'day'

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
                    self._weekly_events[d].append((desc, iid, start, end, cat))
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
        self._display_selection()

    def _remove_event(self, date, desc, iid, repeat, cat):
        year, month, day = date.year, date.month, date.day
        try:
            if not repeat:
                date2 = date.strftime('%Y/%m/%d')
                self._events[date2].remove((desc, iid, cat))
                if not self._events[date2]:
                    del(self._events[date2])
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
                        year = date.year + m // 12
                        end = date.replace(year=year, month=month)
                    else:
                        start_day = date.isocalendar()[2] - 1
                        week_days = [(x - start_day) % 7 for x in repeat['WeekDays']]

                        nb_per_week = len(repeat['WeekDays'])
                        nb_week = nb // nb_per_week
                        rem = nb % nb_per_week
                        end = date + self.timedelta(days=(7 * nb_week + week_days[rem] + 1))
                    end = end.date()
                else:
                    end = None
                if freq == 'year':
                    date2 = date.strftime('*/%m/%d')
                    self._events[date2].remove((desc, iid, start, end, cat))
                    if not self._events[date2]:
                        del(self._events[date2])
                    ev_date = self.date(self._date.year, month, day)
                    if (end is None or ev_date <= end) and (ev_date >= start):
                        self._remove_from_tooltip(ev_date, desc)

                elif freq == 'month':
                    date2 = date.strftime('*/*/%d')
                    self._events[date2].remove((desc, iid, start, end, cat))
                    if not self._events[date2]:
                        del(self._events[date2])
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
                            pass  # month has no day 'day'
                    # current month
                    try:
                        ev_date = self.date(self._date.year, self._date.month, day)
                        if (end is None or ev_date <= end) and (ev_date >= start):
                            self._remove_from_tooltip(ev_date, desc)
                    except ValueError:
                        pass  # month has no day 'day'
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
                            pass  # month has no day 'day'

                elif freq == 'week':
                    cal = self._get_cal(self._date.year, self._date.month)
                    for d in repeat['WeekDays']:
                        self._weekly_events[d].remove((desc, iid, start, end, cat))
                        for w in range(6):
                            self._remove_from_tooltip(cal[w][d], desc)

        except ValueError:
            raise ValueError('Event not in calendar.')

    def _get_date(self, week_row, day):
        year, month = self._date.year, self._date.month
        now = datetime.now() + self.timedelta(minutes=5)
        now = now.replace(minute=(now.minute // 5) * 5)
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
        self.menu.delete(0, 'end')
        day = int(event.widget.cget('text'))
        date = self._get_date(w, day)
        date2 = date.date()

        # --- one time events
        date_str = date.strftime('%Y/%m/%d')
        if date_str in self._events:
            evts = self._events[date_str].copy()
        else:
            evts = []
        # --- yearly events
        date_str = date.strftime('*/%m/%d')
        if date_str in self._events:
            for desc, iid, start, end, cat in self._events[date_str]:
                if start <= date2 and (end is None or end >= date2):
                    evts.append((desc, iid))
        # --- monthly events
        date_str = date.strftime('*/*/%d')
        if date_str in self._events:
            for desc, iid, start, end, cat in self._events[date_str]:
                if start <= date2 and (end is None or end >= date2):
                    evts.append((desc, iid))
        d = date.isocalendar()[2] - 1
        # --- weekly events
        for desc, iid, start, end, cat in self._weekly_events[d]:
            if start <= date2 and (end is None or end >= date2):
                evts.append((desc, iid))

        self.menu.add_command(label=_('New Event'),
                              command=lambda: self.master.master.add(date))
        if evts:
            self.menu.add_separator()
            self.menu.add_separator()
            index_edit = 2
            for vals in evts:
                desc, iid = vals[0], vals[1]
                self.menu.insert_command(index_edit,
                                         label=_("Edit") + " %s" % desc,
                                         command=lambda i=iid: self.master.master.edit(i))
                index_edit += 1
                self.menu.add_command(label=_("Delete") + " %s" % desc,
                                      command=lambda i=iid: self.master.master.delete(i))
        else:
            self.menu.add_separator()
            if date.strftime('%Y/%m/%d') in HOLIDAYS:
                self.menu.add_command(label=_('Remove Holiday'),
                                      command=lambda: self.remove_holiday(date.date()))
            else:
                self.menu.add_command(label=_('Set Holiday'),
                                      command=lambda: self.add_holiday(date.date()))

        self.menu.tk_popup(event.x_root, event.y_root)

    # --- public methods
    def get_events(self, date):
        """ Return the iid of all events occuring on date. """
        evts = []
        for desc, iid, cat in self._events.get(date.strftime('%Y/%m/%d'), []):
            evts.append(iid)
        for desc, iid, start, end, cat in self._events.get(date.strftime('*/%m/%d'), []):
            if start <= date and (end is None or end >= date):
                evts.append(iid)
        for desc, iid, start, end, cat in self._events.get(date.strftime('*/*/%d'), []):
            if start <= date and (end is None or end >= date):
                evts.append(iid)
        y, w, d = date.isocalendar()
        for desc, iid, start, end, cat in self._weekly_events[d - 1]:
            if start <= date and (end is None or end >= date):
                evts.append(iid)
        return evts

    def add_holiday(self, date):
        year = date.year
        HOLIDAYS.add(date.strftime('%Y/%m/%d'))

        if year == self._date.year:
            _, w, d = date.isocalendar()
            w -= self._date.isocalendar()[1]
            w %= 52
            if 0 <= w and w < 6:
                style = self._calendar[w][d - 1].cget('style')
                we_style = 'we.%s.TLabel' % self._style_prefixe
                we_om_style = 'we_om.%s.TLabel' % self._style_prefixe
                normal_style = 'normal.%s.TLabel' % self._style_prefixe
                normal_om_style = 'normal_om.%s.TLabel' % self._style_prefixe
                if style == normal_style:
                    self._calendar[w][d - 1].configure(style=we_style)
                elif style == normal_om_style:
                    self._calendar[w][d - 1].configure(style=we_om_style)

    def remove_holiday(self, date):
        year = date.year
        try:
            HOLIDAYS.remove(date.strftime('%Y/%m/%d'))
            if year == self._date.year:
                _, w, d = date.isocalendar()
                w -= self._date.isocalendar()[1]
                w %= 52
                if 0 <= w and w < 6:
                    style = self._calendar[w][d - 1].cget('style')
                    we_style = 'we.%s.TLabel' % self._style_prefixe
                    we_om_style = 'we_om.%s.TLabel' % self._style_prefixe
                    normal_style = 'normal.%s.TLabel' % self._style_prefixe
                    normal_om_style = 'normal_om.%s.TLabel' % self._style_prefixe
                    if style == we_style:
                        self._calendar[w][d - 1].configure(style=normal_style)
                    elif style == we_om_style:
                        self._calendar[w][d - 1].configure(style=normal_om_style)
        except ValueError:
            raise ValueError('%s is not a holiday.' % format_date(date, locale=self["locale"]))

    def add_event(self, event):
        start = event['Start']
        end = event['End']
        if not event["WholeDay"]:
            deb = format_time(start, locale=self["locale"])
            fin = format_time(end, locale=self["locale"])
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
            deb = format_time(start, locale=self["locale"])
            fin = format_time(end, locale=self["locale"])
            desc = '➢ %s - %s %s' % (deb, fin, event['Summary'])
        else:
            desc = '➢ %s' % event['Summary']
        repeat = event['Repeat']
        dt = end - start
        for d in range(dt.days + 1):
            self._remove_event(start + self.timedelta(days=d),
                               desc, event.iid, repeat, event['Category'])

    def bind(self, *args):
        Calendar.bind(self, *args)
        header = self._header_month.master.master
        header.bind(*args)
        for widget in header.children.values():
            widget.bind(*args)
            for w in widget.children.values():
                w.bind(*args)
