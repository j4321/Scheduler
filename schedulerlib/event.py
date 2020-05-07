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


Event class
"""
from subprocess import run
from datetime import timedelta, datetime, time, date, timezone

from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

from schedulerlib.constants import NOTIF_PATH, TASK_STATE, CONFIG,\
    format_date, format_datetime


class Event:
    def __init__(self, scheduler, iid=None, **kw):
        d = datetime.now() + timedelta(minutes=5)
        d = d.replace(minute=(d.minute // 5) * 5)
        d = kw.pop('Start', d)
        self.scheduler = scheduler
        defaults = {'Summary': '', 'Place': '', 'Description': '',
                    'Start': d, 'End': d + timedelta(hours=1), 'Task': False,
                    'Repeat': {}, 'WholeDay': False, 'Reminders': {},
                    'Category': CONFIG.options('Categories')[0]}
        defaults.update(kw)
        self._properties = defaults
        self.iid = iid

    @classmethod
    def from_vevent(cls, vevent, scheduler, category):
        """Create Event from icalendar VEVENT"""
        props = {"Category": category}
        props['Summary'] = vevent.get('summary')
        props['Description'] = vevent.get('description')
        props['Place'] = vevent.get('location')
        print(vevent.get('dtstart').dt)
        start = vevent.get('dtstart').dt
        end = vevent.get('dtend').dt
        if isinstance(start, datetime):
            props['Start'] = start.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)
            props['End'] = end.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)
            props['WholeDay'] = False
        else:
            props['Start'] = datetime(start.year, start.month, start.day)
            props['End'] = datetime(end.year, end.month, end.day, 23, 59, 0)
            props['WholeDay'] = True
        ev = cls(scheduler, iid=vevent.get("uid"), **props)
        for component in vevent.walk():
            if component.name == 'VALARM':
                action = component.get("action")
                if action and action != "NONE":
                    dt = props['Start'] + component.get("trigger").dt
                    ev.reminder_add(dt)
        return ev

    def __str__(self):
        return '%s\n%s - %s - %s' % self.values()[:-1]

    def __getitem__(self, item):
        if item in self._properties:
            return self._properties[item]
        else:
            raise AttributeError("Event object has no attribute %s." % item)

    def __setitem__(self, item, value):
        if item in ['Summary', 'Place', 'Description', 'Category']:
            self._properties[item] = str(value)
        elif item in ['Start', 'End']:
            if type(value) is datetime:
                self._properties[item] = value
            else:
                self._properties[item] = datetime.strptime(value, '%Y-%m-%d %H:%M')
        elif item == 'WholeDay':
            self._properties[item] = bool(value)
        elif item == 'Repeat':
            self._properties[item] = value
        elif item == 'Task':
            vals = [False]
            vals.extend(TASK_STATE.keys())
            vals.extend(['{}%'.format(i) for i in range(0, 110, 10)])
            if value in vals:
                self._properties['Task'] = value
            else:
                raise ValueError("Unrecognized Task option %s." % value)
        elif item == 'Reminders':
            raise AttributeError("This attribute cannot be set, use 'reminder_add'/'reminder_remove' instead.")
        else:
            raise AttributeError("Event object has no attribute %s." % item)

    def reminder_add(self, date):
        repeat = self._properties['Repeat']

        if repeat:
            cron_prop = {}
            cron_prop['start_date'] = date
            cron_prop['hour'] = date.hour
            cron_prop['minute'] = date.minute
            cron_prop['second'] = date.second
            cron_prop['year'] = '*'
            if repeat['Limit'] == 'until':
                end = repeat['EndDate']
                cron_prop['end_date'] = date.replace(year=end.year,
                                                     month=end.month,
                                                     day=end.day)
            elif repeat['Limit'] == 'after':
                nb = repeat['NbTimes'] - 1  # date is the first time
                if repeat['Frequency'] == 'year':
                    cron_prop['end_date'] = date.replace(year=date.year + nb) + timedelta(hours=1)
                elif repeat['Frequency'] == 'month':
                    m = date.month + nb
                    month = m % 12
                    year = date.year + m // 12
                    cron_prop['end_date'] = date.replace(year=year, month=month) + timedelta(hours=1)
                else:
                    start_day = date.isocalendar()[2] - 1
                    week_days = [(x - start_day) % 7 for x in repeat['WeekDays']]

                    nb_per_week = len(repeat['WeekDays'])
                    nb_week = nb // nb_per_week
                    rem = nb % nb_per_week
                    cron_prop['end_date'] = date + timedelta(days=(7 * nb_week + week_days[rem] + 1))
            else:
                cron_prop['end_date'] = None

            if repeat['Frequency'] == 'week':
                cron_prop['day_of_week'] = ','.join([str(i) for i in repeat['WeekDays']])
                cron_prop['month'] = '*'
            elif repeat['Frequency'] == 'month':
                cron_prop['day'] = date.day
                cron_prop['month'] = '*'
            else:
                cron_prop['day'] = date.day
                cron_prop['month'] = date.month

            job = self.scheduler.add_job(run, trigger=CronTrigger(**cron_prop),
                                         args=(['python3', NOTIF_PATH, str(self)],))
        else:
            job = self.scheduler.add_job(run, trigger=DateTrigger(date),
                                         args=(['python3', NOTIF_PATH, str(self)],))
        self._properties['Reminders'][job.id] = date

    def reminder_remove(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
            del(self._properties['Reminders'][job_id])
        except (JobLookupError, KeyError):
            pass

    def reminder_remove_all(self):
        ids = list(self._properties['Reminders'].keys())
        for job_id in ids:
            self.reminder_remove(job_id)

    def values(self):
        """ return the values (Summary, Place, Start, End)
            to put in the main window treeview """
        locale = CONFIG.get("General", "locale")
        if self['WholeDay']:
            start = format_date(self['Start'], locale=locale)
            end = format_date(self['End'], locale=locale)
        else:
            start = format_datetime(self['Start'], locale=locale)
            end = format_datetime(self['End'], locale=locale)
        return self['Summary'], self['Place'], start, end, self['Category']

    def get(self, key):
        return self._properties.get(key)

    def get_start_time(self):
        start = self['Start']
        return time(hour=start.hour, minute=start.minute, second=start.second)

    def get_last_date(self):
        """ Return the start date of the last occurence of the event """
        repeat = self['Repeat']
        if not repeat:
            return self['Start']
        else:
            freq = repeat['Frequency']
            date = self['Start']
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
                return end
            else:
                return None

    def keys(self):
        return self._properties.keys()

    def items(self):
        return self._properties.items()

    def to_dict(self):
        ev = {"iid": self.iid}
        ev.update(self._properties)
        return ev