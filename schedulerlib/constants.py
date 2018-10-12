#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2018 Juliette Monsel <j_4321@protonmail.com>
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
import warnings
from subprocess import check_output

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
BACKUP_PATH = os.path.join(LOCAL_PATH, 'backup', 'data.backup%i')
CONFIG_PATH = os.path.join(LOCAL_PATH, 'scheduler.ini')
LOG_PATH = os.path.join(LOCAL_PATH, 'scheduler.log')
NOTIF_PATH = os.path.join(PATH, 'notif.py')
JOBSTORE = os.path.join(LOCAL_PATH, 'scheduler.sqlite')

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
    CONFIG.set('General', 'trayicon', '')

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

    CONFIG.add_section('Categories')
    CONFIG.set('Categories', 'default', 'white, #186CBE')

locale.setlocale(locale.LC_ALL, CONFIG.get('General', 'locale'))

HOLIDAYS = set(CONFIG.get('Calendar', 'holidays').split(', '))
if '' in HOLIDAYS:
    HOLIDAYS.remove('')

ICON_NAME = "scheduler-tray"  # gtk / qt tray icon
ICON48 = os.path.join(IMAGES_PATH, 'icon48.png')
TKTRAY_ICON = os.path.join(IMAGES_PATH, 'scheduler.png')
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
SCROLL_ALPHA = os.path.join(IMAGES_PATH, "scroll.png")


TASK_STATE = {'Pending': '⌛', 'In Progress': '✎', 'Completed': '✔', 'Cancelled': '✗'}

CATEGORIES = {cat: CONFIG.get('Categories', cat).split(', ')
              for cat in CONFIG.options('Categories')}


# --- system tray icon
def get_available_gui_toolkits():
    """Check which gui toolkits are available to create a system tray icon."""
    toolkits = {'gtk': True, 'qt': True, 'tk': True}
    b = False
    try:
        import gi
        b = True
    except ImportError:
        toolkits['gtk'] = False

    try:
        import PyQt5
        b = True
    except ImportError:
        try:
            import PyQt4
            b = True
        except ImportError:
            try:
                import PySide
                b = True
            except ImportError:
                toolkits['qt'] = False

    tcl_packages = check_output(["tclsh",
                                 os.path.join(PATH, "packages.tcl")]).decode().strip().split()
    toolkits['tk'] = "tktray" in tcl_packages
    b = b or toolkits['tk']
    if not b:
        raise ImportError("No GUI toolkits available to create the system tray icon.")
    return toolkits


TOOLKITS = get_available_gui_toolkits()
GUI = CONFIG.get("General", "trayicon", fallback='').lower()

if not TOOLKITS.get(GUI):
    DESKTOP = os.environ.get('XDG_CURRENT_DESKTOP')
    if DESKTOP == 'KDE':
        if TOOLKITS['qt']:
            GUI = 'qt'
        else:
            warnings.warn("No version of PyQt was found, falling back to another GUI toolkits so the system tray icon might not behave properly in KDE.")
            GUI = 'gtk' if TOOLKITS['gtk'] else 'tk'
    else:
        if TOOLKITS['gtk']:
            GUI = 'gtk'
        elif TOOLKITS['qt']:
            GUI = 'qt'
        else:
            GUI = 'tk'
    CONFIG.set("General", "trayicon", GUI)
print('GUI', GUI)

if GUI == 'tk':
    ICON = TKTRAY_ICON
else:
    ICON = ICON_NAME


# --- compatibility
def add_trace(variable, mode, callback):
    """
    Add trace to variable.

    Ensure compatibility with old and new trace method.
    mode: "read", "write", "unset" (new syntax)
    """
    try:
        return variable.trace_add(mode, callback)
    except AttributeError:
        # fallback to old method
        return variable.trace(mode[0], callback)


def remove_trace(variable, mode, cbname):
    """
    Remove trace from variable.

    Ensure compatibility with old and new trace method.
    mode: "read", "write", "unset" (new syntax)
    """
    try:
        variable.trace_remove(mode, cbname)
    except AttributeError:
        # fallback to old method
        variable.trace_vdelete(mode[0], cbname)


def info_trace(variable):
    """
    Remove trace from variable.

    Ensure compatibility with old and new trace method.
    mode: "read", "write", "unset" (new syntax)
    """
    try:
        return variable.trace_info()
    except AttributeError:
        return variable.trace_vinfo()



# --- functions
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


def is_color_light(r, g, b):
    p = ((0.299 * r ** 2 + 0.587 * g ** 2 + 0.114 * b ** 2) ** 0.5) / 255
    return p > 0.5


def active_color(r, g, b, output='HTML'):
    """Return a lighter shade of color (RGB triplet with value max 255) in HTML format."""
    if is_color_light(r, g, b):
        r *= 3 / 4
        g *= 3 / 4
        b *= 3 / 4
    else:
        r += (255 - r) / 3
        g += (255 - g) / 3
        b += (255 - b) / 3
    if output == 'HTML':
        return ("#%2.2x%2.2x%2.2x" % (round(r), round(g), round(b))).upper()
    else:
        return (round(r), round(g), round(b))


def save_config():
    CONFIG.set('Calendar', 'holidays', ', '.join(HOLIDAYS))
    with open(CONFIG_PATH, 'w') as file:
        CONFIG.write(file)
