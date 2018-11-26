# IPython log file

import sqlite3
import pickle
import datetime

db = sqlite3.connect('scheduler_test.db')
cursor = db.cursor()

with open('scheduler_config/data', 'rb') as fich:
    data = pickle.Unpickler(fich).load()

cursor.execute('''
    CREATE TABLE events(id INTEGER PRIMARY KEY, summary TEXT NOT NULL,
                        place TEXT, description TEXT, start TEXT NOT NULL,
                        end TEXT NOT NULL, category TEXT NOT NULL,
                        task INTEGER, whole_day INTEGER,
                        repeat_freq TEXT, repeat_start TEXT, repeat_end TEXT,
                        reminders TEXT)
''')
db.commit()


def data_to_db():
    db = sqlite3.connect('scheduler_test.db')
    cursor = db.cursor()
    for e in data:
        ev = {'summary': e['Summary'], 'place': e['Place'],
              'description': e['Description'],
              'start': e['Start'].strftime('%Y-%m-%d %H:%M'),
              'end': e['End'].strftime('%Y-%m-%d %H:%M'),
              'category': e['Category'], 'task': int(e['Task']),
              'whole_day': int(e['WholeDay']),
              'reminders': ", ".join(["%s:%s" % (id, d.strftime('%Y-%m-%d %H:%M')) for id, d in e['Reminders'].items()])}
        ev.update(convert_repeat(e))
        cursor.execute('''INSERT INTO events(summary, place, description, start, end, category, task, whole_day, repeat_freq, repeat_start, repeat_end, reminders)
                          VALUES(:summary, :place, :description, :start, :end, :category, :task, :whole_day, :repeat_freq, :repeat_start, :repeat_end, :reminders)''', ev)
    db.commit()


def convert_repeat(e):
    rep = {}
    repeat = e['Repeat']
    if not repeat:
        rep = {'repeat_freq': 'single', 'repeat_start': '', 'repeat_end': ''}
    else:
        rep['repeat_start'] = e['Start'].strftime('%Y-%m-%d')
        freq = repeat['Frequency']
        if freq == 'week':
            rep['repeat_freq'] = ' '.join([str(i) for i in repeat['WeekDays']])
        else:
            rep['repeat_freq'] = repeat['frequency']
        if repeat['Limit'] == 'always':
            rep['repeat_end'] = ''
        elif repeat['Limit'] == 'until':
            rep['repeat_end'] = repeat['EndDate'].strftime('%Y-%m-%d')
        else:
            # after n times
            n = repeat['NbTimes'] - 1
            start = e['Start']
            if freq == 'year':
                end = start.replace(year=start.year + n)
            elif freq == 'month':
                m = date.month + n
                month = m % 12
                year = date.year + m//12
                end = start.replace(month=month, year=year)
            else:
                # week
                wd = repeat['WeekDays']
                end = start + datetime.timedelta(days=7*n + wd[-1] - wd[0])
            rep['repeat_end'] = end.strftime('%Y-%m-%d')

    return rep
with open('scheduler_config/data', 'rb') as fich:
    data = pickle.Unpickler(fich).load()

db = sqlite3.connect('scheduler_test.db')
cursor = db.cursor()
cursor.execute('''
CREATE TABLE events(id INTEGER PRIMARY KEY, summary TEXT NOT NULL, place TEXT, description TEXT, start TEXT NOT NULL, end TEXT NOT NULL, category TEXT NOT NULL, task INTEGER, whole_day INTEGER, repeat_freq TEXT, repeat_start TEXT, repeat_end TEXT, reminders TEXT)
''')
db.commit()
for e in data:
    ev = {'summary': e['Summary'], 'place': e['Place'], 'description': e['Description'], 'start': e['Start'].strftime('%Y-%m-%d %H:%M'), 'end': e['End'].strftime('%Y-%m-%d %H:%M'), 'category': e['Category'], 'task': int(e['Task']), 'whole_day': int(e['WholeDay']),  'reminders': ", ".join(["%s:%s" % (id, d.strftime('%Y-%m-%d %H:%M')) for id, d in e['Reminders'].items()])}
    ev.update(convert_repeat(e))
    cursor.execute('''INSERT INTO events(summary, place, description, start, end, category, task, whole_day, repeat_freq, repeat_start, repeat_end, reminders)
              VALUES(:summary, :place, :description, :start, :end, :category, :task, :whole_day, :repeat_freq, :repeat_start, :repeat_end, :reminders)''', ev)
    db.commit()
get_ipython().magic('cd /home/juliette/.scheduler/')
get_ipython().magic('ls ')
with open('data', 'rb') as fich:
    data = pickle.Unpickler(fich).load()

db = sqlite3.connect('scheduler.db')
cursor = db.cursor()
cursor.execute('''
CREATE TABLE events(id INTEGER PRIMARY KEY, summary TEXT NOT NULL, place TEXT, description TEXT, start TEXT NOT NULL, end TEXT NOT NULL, category TEXT NOT NULL, task INTEGER, whole_day INTEGER, repeat_freq TEXT, repeat_start TEXT, repeat_end TEXT, reminders TEXT)
''')
db.commit()
for e in data:
    ev = {'summary': e['Summary'], 'place': e['Place'], 'description': e['Description'], 'start': e['Start'].strftime('%Y-%m-%d %H:%M'), 'end': e['End'].strftime('%Y-%m-%d %H:%M'), 'category': e['Category'], 'task': int(e['Task']), 'whole_day': int(e['WholeDay']),  'reminders': ", ".join(["%s:%s" % (id, d.strftime('%Y-%m-%d %H:%M')) for id, d in e['Reminders'].items()])}
    ev.update(convert_repeat(e))
    cursor.execute('''INSERT INTO events(summary, place, description, start, end, category, task, whole_day, repeat_freq, repeat_start, repeat_end, reminders)
              VALUES(:summary, :place, :description, :start, :end, :category, :task, :whole_day, :repeat_freq, :repeat_start, :repeat_end, :reminders)''', ev)
    db.commit()

db = sqlite3.connect('scheduler.db')
cursor = db.cursor()
cursor.execute('''
CREATE TABLE events(id INTEGER PRIMARY KEY, summary TEXT NOT NULL, place TEXT, description TEXT, start TEXT NOT NULL, end TEXT NOT NULL, category TEXT NOT NULL, task TEXT, whole_day INTEGER, repeat_freq TEXT, repeat_start TEXT, repeat_end TEXT, reminders TEXT)
''')
db.commit()
for e in data:
    ev = {'summary': e['Summary'],
          'place': e['Place'],
          'description': e['Description'],
          'start': e['Start'].strftime('%Y-%m-%d %H:%M'),
          'end': e['End'].strftime('%Y-%m-%d %H:%M'),
          'category': e['Category'],
          'whole_day': int(e['WholeDay']),
          'reminders': ", ".join(["%s:%s" % (id, d.strftime('%Y-%m-%d %H:%M')) for id, d in e['Reminders'].items()])}
    ev.update(convert_repeat(e))
    task = e['Task']
    if not task:
        task = ""
    ev['task'] = task
    cursor.execute('''INSERT INTO events(summary, place, description, start, end, category, task, whole_day, repeat_freq, repeat_start, repeat_end, reminders)
              VALUES(:summary, :place, :description, :start, :end, :category, :task, :whole_day, :repeat_freq, :repeat_start, :repeat_end, :reminders)''', ev)
    db.commit()
