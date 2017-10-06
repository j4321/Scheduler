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


Constants and functions.
"""


import os
import logging
from logging.handlers import TimedRotatingFileHandler
import locale
from configparser import ConfigParser
import time
import platform


# --- paths
PATH = os.path.dirname(__file__)

if os.access(PATH, os.W_OK) and os.path.exists(os.path.join(PATH, "images")):
    # the app is not installed
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.dirname(PATH), "scheduler_config")
    IMAGES_PATH = os.path.join(PATH, 'images')
else:
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.expanduser('~'), '.scheduler')
    IMAGES_PATH = "/usr/share/scheduler/images"

if not os.path.isdir(LOCAL_PATH):
        os.mkdir(LOCAL_PATH)

PATH_CONFIG = os.path.join(LOCAL_PATH, "checkmails.ini")
PATH = os.path.dirname(__file__)

PIDFILE = os.path.join(LOCAL_PATH, 'scheduler.pid')

DATA_PATH = os.path.join(LOCAL_PATH, 'data')
DATA_INFO_PATH = os.path.join(LOCAL_PATH, 'data.info')
BACKUP_PATH = os.path.join(LOCAL_PATH, 'backup', 'data.backup%i')
CONFIG_PATH = os.path.join(LOCAL_PATH, 'scheduler.ini')
LOG_PATH = os.path.join(LOCAL_PATH, 'scheduler.log')
NOTIF_PATH = os.path.join(PATH, 'notif.py')
JOBSTORE = os.path.join(LOCAL_PATH, 'scheduler.sqlite')
SYNC_PWD = os.path.join(LOCAL_PATH, '.pwd')

if not os.path.exists(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)

if not os.path.exists(os.path.dirname(BACKUP_PATH)):
    os.mkdir(os.path.dirname(BACKUP_PATH))

# --- log
handler = TimedRotatingFileHandler(LOG_PATH, when='midnight', backupCount=7)
logging.basicConfig(level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[handler])
logging.getLogger().addHandler(logging.StreamHandler())

# --- config file
CONFIG = ConfigParser()

if not CONFIG.read(CONFIG_PATH):
    CONFIG.add_section('General')
    CONFIG.set('General', 'locale', '.'.join(locale.getdefaultlocale()))
    CONFIG.set('General', 'alpha', '0.85')
    CONFIG.set('General', 'backups', '10')

    CONFIG.add_section('Events')
    CONFIG.set('Events', 'geometry', '')
    CONFIG.set('Events', 'font', 'Liberation\ Sans 10')
    CONFIG.set('Events', 'font_title', 'Liberation\ Sans 12 bold')
    CONFIG.set('Events', 'font_day', 'Liberation\ Sans 11 bold')
    CONFIG.set('Events', 'foreground', 'white')
    CONFIG.set('Events', 'background', 'gray10')
    CONFIG.set('Events', 'position', 'normal')

    CONFIG.add_section('Tasks')
    CONFIG.set('Tasks', 'geometry', '')
    CONFIG.set('Tasks', 'font', 'Liberation\ Sans 10')
    CONFIG.set('Tasks', 'font_title', 'Liberation\ Sans 12 bold')
    CONFIG.set('Tasks', 'foreground', 'white')
    CONFIG.set('Tasks', 'background', 'gray10')
    CONFIG.set('Tasks', 'position', 'normal')
    CONFIG.set('Tasks', 'hide_completed', 'False')

    CONFIG.add_section('Timer')
    CONFIG.set('Timer', 'geometry', '')
    CONFIG.set('Timer', 'font_time', 'FreeMono 26')
    CONFIG.set('Timer', 'font_intervals', 'FreeMono 12')
    CONFIG.set('Timer', 'foreground', 'white')
    CONFIG.set('Timer', 'background', 'gray10')
    CONFIG.set('Timer', 'position', 'normal')

    CONFIG.add_section('Calendar')
    CONFIG.set('Calendar', 'holidays', '')
    CONFIG.set('Calendar', 'geometry', '')
    CONFIG.set('Calendar', 'font', '')
    CONFIG.set('Calendar', 'background', '#424242')
    CONFIG.set('Calendar', 'foreground', '#ECECEC')
    CONFIG.set('Calendar', 'bordercolor', 'gray70')
    CONFIG.set('Calendar', 'othermonthforeground', 'gray30')
    CONFIG.set('Calendar', 'othermonthbackground', 'gray93')
    CONFIG.set('Calendar', 'othermonthweforeground', 'gray30')
    CONFIG.set('Calendar', 'othermonthwebackground', 'gray75')
    CONFIG.set('Calendar', 'normalforeground', 'black')
    CONFIG.set('Calendar', 'normalbackground', 'white')
    CONFIG.set('Calendar', 'selectforeground', 'white')
    CONFIG.set('Calendar', 'selectbackground', '#424242')
    CONFIG.set('Calendar', 'weekendforeground', '#424242')
    CONFIG.set('Calendar', 'weekendbackground', 'lightgrey')
    CONFIG.set('Calendar', 'headersforeground', 'black')
    CONFIG.set('Calendar', 'headersbackground', 'gray70')
    CONFIG.set('Calendar', 'tooltipforeground', 'white')
    CONFIG.set('Calendar', 'tooltipbackground', 'black')
    CONFIG.set('Calendar', 'position', 'normal')

    CONFIG.add_section("Sync")
    CONFIG.set("Sync", "on", "False")
    CONFIG.set("Sync", "server_type", "WebDav")
    CONFIG.set("Sync", "server", "")
    CONFIG.set("Sync", "username", "")
    CONFIG.set("Sync", "protocol", "https")
    CONFIG.set("Sync", "port", "443")
    CONFIG.set("Sync", "file", "")

    CONFIG.add_section('Categories')
    CONFIG.set('Categories', 'default', 'white, #186CBE')
elif not CONFIG.has_section("Sync"):
    CONFIG.add_section("Sync")
    CONFIG.set("Sync", "on", "False")
    CONFIG.set("Sync", "server_type", "WebDav")
    CONFIG.set("Sync", "server", "")
    CONFIG.set("Sync", "username", "")
    CONFIG.set("Sync", "protocol", "https")
    CONFIG.set("Sync", "port", "443")
    CONFIG.set("Sync", "file", "")
locale.setlocale(locale.LC_ALL, CONFIG.get('General', 'locale'))

HOLIDAYS = set(CONFIG.get('Calendar', 'holidays').split(', '))
if '' in HOLIDAYS:
    HOLIDAYS.remove('')

ICON48 = os.path.join(IMAGES_PATH, 'icon48.png')
ICON = os.path.join(IMAGES_PATH, 'scheduler.png')
BELL = os.path.join(IMAGES_PATH, 'bell.png')
MOINS = os.path.join(IMAGES_PATH, 'moins.png')
PLUS = os.path.join(IMAGES_PATH, 'plus.png')
DOT = os.path.join(IMAGES_PATH, 'dot.png')
PLAY = os.path.join(IMAGES_PATH, 'play.png')
PAUSE = os.path.join(IMAGES_PATH, 'pause.png')
STOP = os.path.join(IMAGES_PATH, 'stop.png')
CLOSED = os.path.join(IMAGES_PATH, 'closed.png')
OPENED = os.path.join(IMAGES_PATH, 'open.png')
CLOSED_SEL = os.path.join(IMAGES_PATH, 'closed_sel.png')
OPENED_SEL = os.path.join(IMAGES_PATH, 'open_sel.png')


TASK_STATE = {'Pending': '⌛', 'In Progress': '✎', 'Completed': '✔', 'Cancelled': '✗'}

CATEGORIES = {cat: CONFIG.get('Categories', cat).split(', ')
              for cat in CONFIG.options('Categories')}


def backup():
    nb_backup = CONFIG.getint('General', 'backups')
    backups = [int(f.split(".")[-1][6:])
               for f in os.listdir(os.path.dirname(BACKUP_PATH))
               if f[:11] == "data.backup"]
    try:
        if len(backups) < nb_backup:
            os.rename(DATA_PATH, BACKUP_PATH % len(backups))
        else:
            os.remove(BACKUP_PATH % 0)
            for i in range(1, len(backups)):
                os.rename(BACKUP_PATH % i, BACKUP_PATH % (i - 1))
            os.rename(DATA_PATH, BACKUP_PATH % (nb_backup - 1))
    except FileNotFoundError:
        pass


def active_color(r, g, b):
    r += (255 - r) / 3
    g += (255 - g) / 3
    b += (255 - b) / 3
    return ("#%2.2x%2.2x%2.2x" % (round(r), round(g), round(b))).upper()


def save_modif_info(tps=None):
    """ save info about last modifications (machine and time) """
    if tps is None:
        tps = time.time()
    info = platform.uname()
    info = "%s %s %s %s %s\n" % (info.system, info.node, info.release,
                                 info.version, info.machine)
    lines = [info, str(tps)]
    with open(DATA_INFO_PATH, 'w') as fich:
        fich.writelines(lines)
