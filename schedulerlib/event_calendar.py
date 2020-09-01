#!/usr/bin/env python3
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
    def __init__(self, master=None):
        """
        Create an EventCalendar.

        Options are loaded from app config and selectmode is set to 'none'.
        """
        kw = {op: CONFIG.get('Calendar', op) for op in CONFIG.options('Calendar')}
        kw['locale'] = CONFIG.get('General', 'locale')

        tp_fg = kw.pop('tooltipforeground', 'white')
        tp_bg = kw.pop('tooltipbackground', 'black')
        tp_alpha = kw.pop('tooltipalpha', 0.8)
        kw['selectmode'] = 'none'

        self._events = {}
        self._repeated_events = {}
        self._current_month_events = {}
        self._events_tooltips = [[None for i in range(7)] for j in range(6)]

        Calendar.__init__(self, master, class_='EventCalendar', **kw)

        self._cats = {cat: CONFIG.get('Categories', cat).split(', ')
                      for cat in CONFIG.options('Categories')}

        self._properties['tooltipbackground'] = tp_bg
        self._properties['tooltipforeground'] = tp_fg
        self._properties['tooltipalpha'] = tp_alpha

        self.menu = Menu(self)

        for i, week in enumerate(self._calendar):
            for j, day in enumerate(week):
                day.bind('<Double-1>', lambda e, w=i: self._on_dbclick(e, w))
                day.bind('<3>', lambda e, w=i: self._post_menu(e, w))

    def update_style(self):
        self._cats.clear()
        try:
            for cat, val in CONFIG.items('Categories'):
                fg, bg, order = val.split(', ')
                self._cats[cat] = [fg, bg, int(order)]
                style = 'ev_%s.%s.TLabel' % (cat, self._style_prefixe)
                self.style.configure(style, background=bg, foreground=fg)
        except ValueError:  # old config file
            for cat, val in CONFIG.items('Categories'):
                fg, bg = val.split(', ')
                self._cats[cat] = [fg, bg, 0]
                style = 'ev_%s.%s.TLabel' % (cat, self._style_prefixe)
                self.style.configure(style, background=bg, foreground=fg)
        cal = self._get_cal(self._date.year, self._date.month)
        for week_nb in range(6):
            for d in range(7):
                day = cal[week_nb][d]
                evts = self._current_month_events.get(day.strftime('%Y/%m/%d'), [])
                if evts:
                    self._calendar[week_nb][d].configure(style='ev_%s.%s.TLabel' % (self._get_cat(evts),
                                                                                    self._style_prefixe))
        self._display_selection()

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
        """Get calendar for given month of given year."""
        cal = self._cal.monthdatescalendar(year, month)
        next_m = month + 1
        y = year
        if next_m == 13:
            next_m = 1
            y += 1
        if len(cal) < 6:
            if cal[-1][-1].month == month:
                i = 0
            else:
                i = 1
            cal.append(self._cal.monthdatescalendar(y, next_m)[i])
            if len(cal) < 6:
                cal.append(self._cal.monthdatescalendar(y, next_m)[i + 1])
        return cal

    def update_sel(self):
        """Update current day."""
        logging.info('Update current day to %s' % self.date.today())
        prev_sel = self._sel_date
        self._sel_date = self.date.today()
        if prev_sel == self._sel_date:
            return
        if self._sel_date.month != self._date.month:
            self._date = self._sel_date.replace(day=1)
            self._display_calendar()
        else:
            evts = self._current_month_events[prev_sel.strftime('%Y/%m/%d')]
            if not evts:
                self._reset_day(prev_sel)
            else:
                cat = self._get_cat(evts)
                w, d = self._get_day_coords(prev_sel)
                self._calendar[w][d].configure(style='ev_%s.%s.TLabel' % (cat, self._style_prefixe))
        self._display_selection()

    def _display_calendar(self):
        Calendar._display_calendar(self)
        year, month = self._date.year, self._date.month
        cal = self._get_cal(year, month)

        self._current_month_events.clear()
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
        # repeated event
        start, end = cal[0][0], cal[-1][-1]
        for iid, (desc, nbdays, drrule, cat, start_time) in self._repeated_events.items():
            for ev_date in drrule.between(start, end):
                for d in range(nbdays):
                    date = ev_date + self.timedelta(days=d)
                    date2 = date.strftime('%Y/%m/%d')
                    if date2 not in self._current_month_events:
                        self._current_month_events[date2] = []
                    self._current_month_events[date2].append((start_time, desc, iid, cat))
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
                if date not in self._current_month_events:
                    self._current_month_events[date] = []
                self._current_month_events[date].extend(self._events.get(date, []))
                evts = self._current_month_events[date]
                evts.sort()
                if evts:
                    txt = '\n'.join([evt[1] for evt in evts])
                    self._set_tooltip(w, d, txt, self._get_cat(evts))
        self._display_selection()

    def _set_tooltip(self, week_nb, day, txt, cat):
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
            tp.configure(text=txt)

    def _get_cat(self, evts):
        cats = [(self._cats.get(cat, [10000])[-1], start_time, desc, cat) for start_time, desc, iid, cat in evts]
        return sorted(cats)[0][-1]

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
                        cat = self._get_cat(self._current_month_events[date.strftime('%Y/%m/%d')])
                        self._calendar[week_nb][d].configure(style='ev_%s.%s.TLabel' % (cat, self._style_prefixe))
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

    def _show_event(self, date, txt):
        y1, y2 = date.year, self._date.year
        m1, m2 = date.month, self._date.month
        if y1 == y2 or (y1 - y2 == 1 and m1 == 1 and m2 == 12) or (y2 - y1 == 1 and m2 == 1 and m1 == 12):
            _, w, d = date.isocalendar()
            w -= self._date.isocalendar()[1]
            w %= 52
            if w < 6:
                evts = self._current_month_events[date.strftime('%Y/%m/%d')]
                txt = '\n'.join([evt[1] for evt in evts])
                self._set_tooltip(w, d - 1, txt, self._get_cat(evts))

    def _add_event(self, start, nbdays, desc, iid, drrule, cat):
        cal = self._get_cal(self._date.year, self._date.month)
        mstart, mend = cal[0][0], cal[-1][-1]
        start_time = start.time()
        if not drrule:
            for d in range(nbdays):
                date = start + self.timedelta(days=d)
                date2 = date.strftime('%Y/%m/%d')
                if date2 not in self._events:
                    self._events[date2] = []
                self._events[date2].append((start_time, desc, iid, cat))
                if mstart <= date.date() <= mend:
                    if date2 not in self._current_month_events:
                        self._current_month_events[date2] = []
                    self._current_month_events[date2].append((start_time, desc, iid, cat))
                    self._current_month_events[date2].sort()
                    self._show_event(date, desc)
        else:
            self._repeated_events[iid] = (desc, nbdays, drrule, cat, start.time())

            for ev_date in drrule.between(mstart, mend):
                for d in range(nbdays):
                    date = ev_date + self.timedelta(days=d)
                    date2 = date.strftime('%Y/%m/%d')
                    if date2 not in self._current_month_events:
                        self._current_month_events[date2] = []
                    self._current_month_events[date2].append((start_time, desc, iid, cat))
                    self._current_month_events[date2].sort()
                    self._show_event(date, desc)
        self._display_selection()

    def _remove_event(self, start, nbdays, desc, iid, drrule, cat):
        year, month = self._date.year, self._date.month
        start_time = start.time()
        try:
            if not drrule:
                for d in range(nbdays):
                    date = start + self.timedelta(days=d)
                    date2 = date.strftime('%Y/%m/%d')
                    if date2 in self._current_month_events:
                        self._current_month_events[date2].remove((start_time, desc, iid, cat))
                    self._events[date2].remove((start_time, desc, iid, cat))
                    if not self._events[date2]:
                        del(self._events[date2])
                    self._remove_from_tooltip(date, desc)
            else:
                del self._repeated_events[iid]
                cal = self._get_cal(year, month)
                for ev_date in drrule.between(cal[0][0], cal[-1][-1]):
                    for d in range(nbdays):
                        date = ev_date + self.timedelta(days=d)
                        date2 = date.strftime('%Y/%m/%d')
                        if date2 in self._current_month_events:
                            self._current_month_events[date2].remove((start_time, desc, iid, cat))
                        self._remove_from_tooltip(date, desc)

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
        evts = self._current_month_events[date.strftime('%Y/%m/%d')]

        self.menu.add_command(label=_('New Event'),
                              command=lambda: self.master.master.add(date))
        if evts:
            self.menu.add_separator()
            self.menu.add_separator()
            index_edit = 2
            for start_time, desc, iid, cat in evts:
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
        for start_time, desc, iid, cat in self._events.get(date.strftime('%Y/%m/%d'), []):
            evts.append(iid)

        for iid, (desc, nbdays, drrule, cat, start_time) in self._repeated_events.items():
            if drrule.between(date + self.timedelta(days=-nbdays + 1), date):
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
        dt = end - start
        drrule = event.get_rrule()
        self._add_event(start, dt.days + 1, desc, event.iid, drrule, event['Category'])

    def remove_event(self, event):
        start = event['Start']
        end = event['End']
        if not event["WholeDay"]:
            deb = format_time(start, locale=self["locale"])
            fin = format_time(end, locale=self["locale"])
            desc = '➢ %s - %s %s' % (deb, fin, event['Summary'])
        else:
            desc = '➢ %s' % event['Summary']
        drrule = event.get_rrule()
        dt = end - start
        self._remove_event(start, dt.days + 1, desc, event.iid, drrule, event['Category'])

    def bind(self, *args):
        Calendar.bind(self, *args)
        header = self._header_month.master.master
        header.bind(*args)
        for widget in header.children.values():
            widget.bind(*args)
            for w in widget.children.values():
                w.bind(*args)
