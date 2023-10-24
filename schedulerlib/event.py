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


Event class
"""
from subprocess import run
from datetime import timedelta, datetime, time

from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import BaseCombiningTrigger
from apscheduler.jobstores.base import JobLookupError
from babel.dates import get_day_names
from dateutil import rrule as drrule
from dateutil import relativedelta
import icalendar

from schedulerlib.constants import NOTIF_PATH, TASK_STATE, CONFIG,\
    format_date, format_datetime, get_rel_month_day

DRRULE_FREQS = {"year": drrule.YEARLY, "month": drrule.MONTHLY,
                "week": drrule.WEEKLY, "day": drrule.DAILY}
FREQS = {"YEARLY": "year", "MONTHLY": "month", "WEEKLY": "week", "DAILY": "day"}
FREQS_REV = {i: k for k, i in FREQS.items()}

DAYS = {d.upper(): i for i, d in get_day_names("short", locale="en_US").items()}
DAYS_REV = {i: k for k, i in DAYS.items()}

WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

ORDINALS = {-1: 'last', 1: '1st', 2: '2nd', 3: '3rd'}


class MyCronTrigger(BaseCombiningTrigger):
    """CronTrigger with exclusion date field (exdate)."""

    __slots__ = ()

    def __init__(self, year=None, month=None, day=None, week=None, day_of_week=None, hour=None,
                 minute=None, second=None, start_date=None, end_date=None, timezone=None,
                 jitter=None, exdate=None):
        cron_trig = CronTrigger(year, month, day, week, day_of_week, hour,
                                minute, second, start_date, end_date, timezone, jitter)
        triggers = [cron_trig]
        if exdate is not None:
            triggers.extend([DateTrigger(date) for date in exdate])

        BaseCombiningTrigger.__init__(self, triggers, jitter)

    def get_next_fire_time(self, previous_fire_time, now):
        while True:
            fire_time = self.triggers[0].get_next_fire_time(previous_fire_time, now)
            excl_dates = [trigger.get_next_fire_time(previous_fire_time, now)
                          for trigger in self.triggers[1:]]
            if fire_time is None:
                return None
            elif fire_time not in excl_dates:
                return self._apply_jitter(fire_time, self.jitter, now)
            else:
                now = fire_time + timedelta(seconds=1)

    def __str__(self):
        return 'cron_excl[{}]'.format(', '.join(str(trigger) for trigger in self.triggers))



class Rruleset(drrule.rruleset):
    """Like drrule.rruleset but accepts datetime.date as arguments in between() method."""

    def between(self, after, before, inc=True, count=1):
        after_dt = datetime(after.year, after.month, after.day, 0, 0)
        before_dt = datetime(before.year, before.month, before.day, 23, 59)
        return drrule.rrule.between(self, after_dt, before_dt, inc=inc, count=count)


class Event:
    """Event class to store event's information."""

    def __init__(self, scheduler, iid=None, **kw):
        d = datetime.now() + timedelta(minutes=5)
        d = d.replace(minute=(d.minute // 5) * 5)
        d = kw.pop('Start', d)
        self.scheduler = scheduler
        self.rrule = None
        default_cat = CONFIG.get('Calendar', 'default_category')
        defaults = {'Summary': '', 'Place': '', 'Description': '',
                    'Start': d, 'End': d + timedelta(hours=1), 'Task': False,
                    'Repeat': {}, 'WholeDay': False, 'Reminders': {},
                    'Category': default_cat,
                    'ExtCal': ''}  # on-way sync with external calendar (changes made in the local calendar will not be exported to the remote and will be overriden at the next sync)
        defaults.update(kw)
        if not CONFIG.has_option('Categories', defaults['Category']):
            defaults['Category'] = default_cat
        self._properties = defaults
        self.iid = iid
        self.rrule = None
        self.create_rrule()

    @classmethod
    def from_vevent(cls, vevent, scheduler, category, extcal=""):
        """Create Event from icalendar vEvent."""
        props = {"Category": category, "ExtCal": extcal}
        # info
        props['Summary'] = str(vevent.get('summary', ""))
        props['Description'] = str(vevent.get('description', ""))
        props['Place'] = str(vevent.get('location', ""))
        # start / end
        start = vevent['dtstart'].dt
        end = vevent['dtend'].dt
        if isinstance(start, datetime):
            props['Start'] = start.astimezone(tz=None).replace(tzinfo=None)
            props['End'] = end.astimezone(tz=None).replace(tzinfo=None)
            props['WholeDay'] = False
        else:
            props['Start'] = datetime(start.year, start.month, start.day)
            props['End'] = datetime(end.year, end.month, end.day, 23, 59, 0)
            props['WholeDay'] = True
        # repeat
        rrule = vevent.get("rrule")
        if rrule:
            freq = FREQS[rrule.get("freq")[0]]
            count = rrule.get("count")
            if count:
                limit = "after"
                count = count[0]
                until = datetime.now() + timedelta(days=1)
            else:
                count = 1
                until = rrule.get("until")
                if until:
                    until = until[0]
                    limit = "until"
                else:
                    limit = "always"
                    until = datetime.now() + timedelta(days=1)
            mday = "abs"

            if freq == "week":
                byday = [DAYS[d] for d in rrule.get("byday")]
            else:
                byday = [props['Start'].weekday()]
                if freq == "month":
                    bmday = rrule.get("byday")
                    if bmday:
                        day = bmday[0][-2:]
                        wnb = int(bmday[0][:-2])
                        mday = (DAYS[day], wnb)
            try:
                excl = [excl_date.dt.astimezone(tz=None).replace(tzinfo=None)
                        for excl_date in vevent.get('exdate').dts]
            except AttributeError:
                excl = []
            props["Repeat"] = {'Frequency': freq,
                               'Every': rrule.get("interval", [1])[0],
                               'Limit': limit,  # always until after
                               'NbTimes': count,
                               'EndDate': until.date(),
                               'MonthDay': mday,
                               'WeekDays': byday,
                               'ExclDates': excl}

        # reminders
        ev = cls(scheduler, iid=str(vevent.get("uid")), **props)
        for component in vevent.subcomponents:
            if component.name == 'VALARM':
                action = component.get("action")
                if action and action != "NONE":
                    dt = props['Start'] + component.get("trigger").dt
                    ev.reminder_add(dt)
        return ev

    def __str__(self):
        return '{0}\n{1} - {3} - {4}'.format(*self.values())

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
            self.create_rrule()
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
            cron_prop['start_date'] = date - timedelta(minutes=1)
            cron_prop['hour'] = date.hour
            cron_prop['minute'] = date.minute
            cron_prop['second'] = date.second
            cron_prop['exdate'] = repeat.get('ExclDates', [])
            if repeat['Limit'] == 'until':
                end = repeat['EndDate']
                cron_prop['end_date'] = date.replace(year=end.year,
                                                     month=end.month,
                                                     day=end.day) + timedelta(hours=1)
            elif repeat['Limit'] == 'after':
                cron_prop['end_date'] = self.get_last_date() + timedelta(hours=1)
            else:
                cron_prop['end_date'] = None

            every = repeat.get("Every", 1)
            if every > 1:
                every = f"/{every}"
            else:
                every = ""
            if repeat['Frequency'] == 'day':
                cron_prop['day'] = '*' + every
                cron_prop['month'] = '*'
                cron_prop['year'] = '*'
            elif repeat['Frequency'] == 'week':
                cron_prop['day_of_week'] = ','.join([str(i) for i in repeat['WeekDays']])
                cron_prop['week'] = '*' + every
                cron_prop['month'] = '*'
                cron_prop['year'] = '*'
            elif repeat['Frequency'] == 'month':
                mday = repeat.get("MonthDay", "abs")
                if mday == "abs":
                    mday = date.day
                else:
                    # there will be issues if Start is the last month day
                    # and the reminder is days appart
                    wd, rel_mday = get_rel_month_day(date)
                    mday = f"{ORDINALS.get(rel_mday, f'{rel_mday}th')} {WEEKDAYS[wd]}"

                cron_prop['day'] = mday
                cron_prop['month'] = '*' + every
                cron_prop['year'] = '*'
            else:
                cron_prop['day'] = date.day
                cron_prop['month'] = date.month
                cron_prop['year'] = '*' + every

            job = self.scheduler.add_job(run, trigger=MyCronTrigger(**cron_prop),
                                         args=(['python3', NOTIF_PATH, str(self)],))
        else:
            job = self.scheduler.add_job(run, trigger=DateTrigger(date),
                                         args=(['python3', NOTIF_PATH, str(self)],))
        self._properties['Reminders'][job.id] = date

    def reminder_remove(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass
        try:
            del(self._properties['Reminders'][job_id])
        except KeyError:
            pass

    def reminder_remove_all(self):
        ids = list(self._properties['Reminders'].keys())
        for job_id in ids:
            self.reminder_remove(job_id)

    def reminder_refresh_all(self):
        """Delete and reschedule all reminders."""
        reminders = [date for date in self['Reminders'].values()]
        self.reminder_remove_all()
        for date in reminders:
            self.reminder_add(date)

    def values(self):
        """Return the properties (Summary, Place, Category, Start, End, Is recurring, Next occurrence, Calendar)."""
        locale = CONFIG.get("General", "locale")
        next_occurrence = ''
        repeat = self['Repeat']
        is_rec = _('Yes') if repeat else _('No')
        format_func = format_date if self['WholeDay'] else format_datetime
        start = format_func(self['Start'], locale=locale)
        end = format_func(self['End'], locale=locale)
        cal = self["ExtCal"] if self["ExtCal"] else _("local")
        if repeat:
            next_oc = self.rrule.after(datetime.now())
            if next_oc:
                next_occurrence = format_func(next_oc, locale=locale)
        elif self['Start'] > datetime.now():
            next_occurrence = start
        return (self['Summary'], self['Place'], self['Category'], start, end,
                is_rec, next_occurrence, cal)

    def get(self, key, default=None):
        return self._properties.get(key, default)

    def get_start_time(self):
        start = self['Start']
        return time(hour=start.hour, minute=start.minute, second=start.second)

    def get_last_date(self):
        """Return the start date of the last occurence of the event."""
        repeat = self['Repeat']
        if not repeat:
            return self['Start']
        else:
            if repeat["Limit"] == "always":
                return None
            return list(self.get_rrule())[-1]

    def keys(self):
        return self._properties.keys()

    def items(self):
        return self._properties.items()

    def create_rrule(self):
        """Create dateutil.rrule.rruleset corresponding to the repeat properties."""
        repeat = self['Repeat']
        if not repeat:
            self.rrule = None
            return

        self.rrule = Rruleset()
        freq = DRRULE_FREQS[repeat['Frequency']]
        rrule_kw = {"dtstart": self._properties['Start'],
                    "interval": repeat.get("Every", 1),
                    "wkst": relativedelta.MO}
        # limit
        if repeat['Limit'] == 'until':
            rrule_kw["until"] = repeat['EndDate']

        elif repeat['Limit'] == 'after':
            rrule_kw["count"] = repeat['NbTimes']

        # monthly / weekly
        if repeat['Frequency'] == 'month':
            mday = repeat.get("MonthDay", "abs")
            if mday == "abs":
                rrule_kw["bymonthday"] = self._properties['Start'].day
            else:
                day, pos = mday
                rrule_kw["byweekday"] = relativedelta.weekday(day)(pos)
        elif repeat['Frequency'] == 'week':
            rrule_kw["byweekday"] = repeat["WeekDays"]
        rrule = drrule.rrule(freq, **rrule_kw)
        self.rrule.rrule(rrule)
        # excluded dates
        for excl_date in repeat.get('ExclDates', []):
            self.rrule.exdate(excl_date)

    def exclude_date(self, date):
        repeat = self['Repeat']
        if not repeat:
            return
        if 'ExclDates' not in repeat:
            repeat['ExclDates'] = []
        repeat['ExclDates'].append(date)
        self.rrule.exdate(date)
        self.reminder_refresh_all()

    def to_dict(self):
        """Convert event to dictionnary."""
        ev = {"iid": self.iid}
        ev.update(self._properties)
        return ev

    def to_vevent(self):
        """Convert event to icalendar VEVENT."""
        ev = icalendar.Event()
        ev.add("summary", self["Summary"])
        ev.add("description", self["Description"])
        ev.add("location", self["Place"])
        ev.add("uid", self.iid)
        if self['WholeDay']:
            ev.add("dtstart", self['Start'].date())
            ev.add("dtend", self['End'].date())
        else:
            ev.add("dtstart", self['Start'].astimezone(tz=None))
            ev.add("dtend", self['End'].astimezone(tz=None))
        # repeat
        repeat = self["Repeat"]
        if repeat:
            excl = repeat.get('ExclDates', [])
            if excl:
                ev.add('exdate', excl)
            recur_kw = {}
            freq = repeat['Frequency']
            recur_kw["freq"] = FREQS_REV[freq]
            # limit
            if repeat['Limit'] == 'until':
                recur_kw["until"] = repeat['EndDate']
            elif repeat['Limit'] == 'after':
                recur_kw["count"] = repeat['NbTimes']
            recur_kw["interval"] = repeat['Every']
            # freq
            if freq == "week":
                recur_kw["byday"] = [DAYS_REV[d] for d in repeat["WeekDays"]]
            elif freq == "month":
                mday = repeat["MonthDay"]
                if mday == "abs":
                    recur_kw["bymonthday"] = self['Start'].day
                else:
                    day, pos = mday
                    recur_kw["byday"] = [f"{pos}{DAYS_REV[day]}"]
            ev.add("rrule", icalendar.vRecur(**recur_kw))

        return ev

    def occurs_between(self, after, before):
        """Return whether the event (start date) occurs between after and before."""

        if self.rrule:
            return len(self.rrule.between(after, before)) > 0
        else:
            after_dt = datetime(after.year, after.month, after.day, 0, 0)
            before_dt = datetime(before.year, before.month, before.day, 23, 59)
            return after_dt <= self['Start'] <= before_dt
