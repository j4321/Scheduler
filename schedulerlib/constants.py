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

The images in ICONS were taken from "icons.tcl":

    A set of stock icons for use in Tk dialogs. The icons used here
    were provided by the Tango Desktop project which provides a
    fied set of high quality icons licensed under the
    Creative Commons Attribution Share-Alike license
    (http://creativecommons.org/licenses/by-sa/3.0/)

    See http://tango.freedesktop.org/Tango_Desktop_Project

    Copyright (c) 2009 Pat Thoyts <patthoyts@users.sourceforge.net>

Constants and functions.
"""


import os
import logging
from logging.handlers import TimedRotatingFileHandler
import locale
from configparser import ConfigParser
import warnings
import gettext
import matplotlib
from tkinter import Toplevel
from tkinter.ttk import Label, Entry, Button
from subprocess import check_output, CalledProcessError
from tkinter import filedialog
from tkinter import colorchooser

APP_NAME = "scheduler"

# --- paths
PATH = os.path.dirname(__file__)

if os.access(PATH, os.W_OK) and os.path.exists(os.path.join(PATH, "images")):
    # the app is not installed
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.dirname(PATH), "scheduler_config")
    PATH_IMAGES = os.path.join(PATH, 'images')
    PATH_SOUNDS = os.path.join(PATH, 'sounds')
    PATH_LOCALE = os.path.join(PATH, "locale")
else:
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.expanduser('~'), '.scheduler')
    PATH_LOCALE = "/usr/share/locale"
    PATH_IMAGES = "/usr/share/scheduler/images"
    PATH_SOUNDS = "/usr/share/scheduler/sounds"

if not os.path.isdir(LOCAL_PATH):
        os.mkdir(LOCAL_PATH)

PATH_CONFIG = os.path.join(LOCAL_PATH, "scheduler.ini")
PATH_STATS = os.path.join(LOCAL_PATH, "pomodoro_stats.sqlite")
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

# --- stat colors
CMAP = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#17becf', '#ff00ff', '#7f7f7f', '#bcbd22', '#9467bd']

# --- log
handler = TimedRotatingFileHandler(LOG_PATH, when='midnight', backupCount=7)
logging.basicConfig(level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[handler])
logging.getLogger().addHandler(logging.StreamHandler())

# --- config
CONFIG = ConfigParser()

if not CONFIG.read(CONFIG_PATH):
    CONFIG.add_section('General')
    CONFIG.set('General', 'locale', '.'.join(locale.getdefaultlocale()))
    CONFIG.set('General', 'backups', '10')
    CONFIG.set('General', 'trayicon', '')
    CONFIG.set("General", "language", "")
    CONFIG.set("General", "eyes_interval", "20")
    CONFIG.set("General", "soundplayer", "")

    CONFIG.add_section('Reminders')
    CONFIG.set('Reminders', 'window', 'True')
    CONFIG.set('Reminders', 'window_alpha', '0.75')
    CONFIG.set('Reminders', 'window_bg', 'gray10')
    CONFIG.set('Reminders', 'window_fg', 'white')
    CONFIG.set('Reminders', 'window_bg_alternate', 'gray30')
    CONFIG.set('Reminders', 'window_fg_alternate', 'red')
    CONFIG.set('Reminders', 'notification', 'True')
    CONFIG.set('Reminders', 'mute', 'True')
    CONFIG.set('Reminders', 'alarm', os.path.join(PATH_SOUNDS, 'alarm.wav'))
    CONFIG.set('Reminders', 'blink', 'True')
    CONFIG.set('Reminders', 'timeout', '5')

    CONFIG.add_section('Events')
    CONFIG.set('Events', 'geometry', '')
    CONFIG.set('Events', 'visible', 'True')
    CONFIG.set('Events', 'alpha', '0.85')
    CONFIG.set('Events', 'font', 'Liberation\ Sans 10')
    CONFIG.set('Events', 'font_title', 'Liberation\ Sans 12 bold')
    CONFIG.set('Events', 'font_day', 'Liberation\ Sans 11 bold')
    CONFIG.set('Events', 'foreground', 'white')
    CONFIG.set('Events', 'background', 'gray10')
    CONFIG.set('Events', 'position', 'normal')

    CONFIG.add_section('Tasks')
    CONFIG.set('Tasks', 'geometry', '')
    CONFIG.set('Tasks', 'visible', 'True')
    CONFIG.set('Tasks', 'alpha', '0.85')
    CONFIG.set('Tasks', 'font', 'Liberation\ Sans 10')
    CONFIG.set('Tasks', 'font_title', 'Liberation\ Sans 12 bold')
    CONFIG.set('Tasks', 'foreground', 'white')
    CONFIG.set('Tasks', 'background', 'gray10')
    CONFIG.set('Tasks', 'position', 'normal')
    CONFIG.set('Tasks', 'hide_completed', 'False')

    CONFIG.add_section('Timer')
    CONFIG.set('Timer', 'geometry', '')
    CONFIG.set('Timer', 'visible', 'True')
    CONFIG.set('Timer', 'alpha', '0.85')
    CONFIG.set('Timer', 'font_time', 'FreeMono 26')
    CONFIG.set('Timer', 'font_intervals', 'FreeMono 12')
    CONFIG.set('Timer', 'foreground', 'white')
    CONFIG.set('Timer', 'background', 'gray10')
    CONFIG.set('Timer', 'position', 'normal')

    CONFIG.add_section('Calendar')
    CONFIG.set('Calendar', 'holidays', '')
    CONFIG.set('Calendar', 'geometry', '')
    CONFIG.set('Calendar', 'visible', 'True')
    CONFIG.set('Calendar', 'alpha', '0.85')
    CONFIG.set('Calendar', 'font', 'TkDefaultFont 8')
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

if not CONFIG.has_section('Pomodoro'):
    CONFIG.add_section('Pomodoro')
    CONFIG.set('Pomodoro', 'geometry', '')
    CONFIG.set('Pomodoro', 'visible', 'True')
    CONFIG.set('Pomodoro', 'alpha', '0.85')
    CONFIG.set('Pomodoro', 'foreground', 'white')
    CONFIG.set('Pomodoro', 'background', 'gray10')
    CONFIG.set('Pomodoro', 'position', 'normal')
    CONFIG.set("Pomodoro", "font", "FreeMono 48")
    CONFIG.set("Pomodoro", "work_time", "25")
    CONFIG.set("Pomodoro", "work_bg", "#ffffff")
    CONFIG.set("Pomodoro", "work_fg", "#000000")
    CONFIG.set("Pomodoro", "break_time", "5")
    CONFIG.set("Pomodoro", "break_bg", "#77ABE2")
    CONFIG.set("Pomodoro", "break_fg", "#000000")
    CONFIG.set("Pomodoro", "rest_time", "20")
    CONFIG.set("Pomodoro", "rest_bg", "#FF7A40")
    CONFIG.set("Pomodoro", "rest_fg", "#000000")
    CONFIG.set("Pomodoro", "beep", os.path.join(PATH_SOUNDS, 'ting.wav'))
    CONFIG.set("Pomodoro", "mute", "False")

    CONFIG.add_section("PomodoroTasks")

if not CONFIG.has_section('Reminders'):
    CONFIG.add_section('Reminders')
    CONFIG.set('Reminders', 'window', 'True')
    CONFIG.set('Reminders', 'window_alpha', '0.75')
    CONFIG.set('Reminders', 'window_bg', 'gray10')
    CONFIG.set('Reminders', 'window_fg', 'white')
    CONFIG.set('Reminders', 'window_bg_alternate', 'gray30')
    CONFIG.set('Reminders', 'window_fg_alternate', 'red')
    CONFIG.set('Reminders', 'notification', 'True')
    CONFIG.set('Reminders', 'mute', 'True')
    CONFIG.set('Reminders', 'alarm', os.path.join(PATH_SOUNDS, 'alarm.wav'))
    CONFIG.set('Reminders', 'blink', 'True')
    CONFIG.set('Reminders', 'timeout', '5')


def save_config():
    CONFIG.set('Calendar', 'holidays', ', '.join(HOLIDAYS))
    with open(CONFIG_PATH, 'w') as file:
        CONFIG.write(file)


# --- language
locale.setlocale(locale.LC_ALL, CONFIG.get('General', 'locale'))

LANGUAGE = CONFIG.get('General', 'language', fallback='')

LANGUAGES = {"fr": "Français", "en": "English"}
REV_LANGUAGES = {val: key for key, val in LANGUAGES.items()}

if LANGUAGE not in LANGUAGES:
    # Check the default locale
    LANGUAGE = locale.getlocale()[0].split('_')[0]
    if LANGUAGE in LANGUAGES:
        CONFIG.set("General", "language", LANGUAGE)
    else:
        CONFIG.set("General", "language", "en")

gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
gettext.bindtextdomain(APP_NAME, PATH_LOCALE)
gettext.textdomain(APP_NAME)

gettext.translation(APP_NAME, PATH_LOCALE,
                    languages=[LANGUAGE],
                    fallback=True).install()

FREQ_REV_TRANSLATION = {_("hours"): "hours", _("minutes"): "minutes", _("days"): "days"}

# --- retrieve holidays
HOLIDAYS = set(CONFIG.get('Calendar', 'holidays').split(', '))
if '' in HOLIDAYS:
    HOLIDAYS.remove('')

# --- default pomodoro task
if not CONFIG.options("PomodoroTasks"):
    # task = color
    CONFIG.set("PomodoroTasks", _("Work"), CMAP[0])

# --- default sound player
if not CONFIG.get("General", "soundplayer", fallback=''):
    if os.path.exists("/usr/bin/aplay"):
        CONFIG.set("General", "soundplayer", "aplay")
    elif os.path.exists("/usr/bin/paplay"):
        CONFIG.set("General", "soundplayer", "paplay")
    elif os.path.exists("/usr/bin/mpg123"):
        CONFIG.set("General", "soundplayer", "mpg123")
    elif os.path.exists("/usr/bin/cvlc"):
        CONFIG.set("General", "soundplayer", "cvlc")
    else:
        top = Toplevel()
        top.resizable((0, 0))
        top.title(_("Sound configuration"))
        Label(top, text=_("The automatic detection of command line soundplayer has failed. \
If you want to hear the beep between work sessions and breaks, please give the \
name of a command line soundplayer installed on your system. If you do not know, \
you can install mpg123.")).grid(row=0, columnspan=2)
        player = Entry(top, justify='center')
        player.grid(row=1, columnspan=2, sticky="ew")

        def valide():
            CONFIG.set("General", "soundplayer", player.get())
            top.destroy()

        Button(top, _("Cancel"), command=top.destroy).grid(row=2, column=0)
        Button(top, _("Ok"), command=valide).grid(row=2, column=1)


# --- images
ICON_NAME = "scheduler-tray"  # gtk / qt tray icon
ICON48 = os.path.join(PATH_IMAGES, 'icon48.png')
TKTRAY_ICON = os.path.join(PATH_IMAGES, 'scheduler.png')
IM_BELL = os.path.join(PATH_IMAGES, 'bell.png')
IM_MOINS = os.path.join(PATH_IMAGES, 'moins.png')
IM_PLUS = os.path.join(PATH_IMAGES, 'plus.png')
IM_DOT = os.path.join(PATH_IMAGES, 'dot.png')
IM_PLAY = os.path.join(PATH_IMAGES, 'play.png')
IM_PAUSE = os.path.join(PATH_IMAGES, 'pause.png')
STOP = os.path.join(PATH_IMAGES, 'stop.png')
IM_POMODORO = os.path.join(PATH_IMAGES, "tomate.png")
IM_GRAPH = os.path.join(PATH_IMAGES, "graph.png")
IM_COLOR = os.path.join(PATH_IMAGES, "color.png")
IM_SOUND = os.path.join(PATH_IMAGES, "son.png")
IM_MUTE = os.path.join(PATH_IMAGES, "mute.png")
IM_SOUND_DIS = os.path.join(PATH_IMAGES, "son_dis.png")
IM_MUTE_DIS = os.path.join(PATH_IMAGES, "mute_dis.png")
IM_CLOSED = os.path.join(PATH_IMAGES, 'closed.png')
IM_OPENED = os.path.join(PATH_IMAGES, 'open.png')
IM_CLOSED_SEL = os.path.join(PATH_IMAGES, 'closed_sel.png')
IM_OPENED_SEL = os.path.join(PATH_IMAGES, 'open_sel.png')
IM_LAYOUT = os.path.join(PATH_IMAGES, 'layout.png')
IM_GRID = os.path.join(PATH_IMAGES, 'grid.png')
IM_SCROLL_ALPHA = os.path.join(PATH_IMAGES, "scroll.png")
IM_EYE = os.path.join(PATH_IMAGES, "yeux.svg")
IM_START = os.path.join(PATH_IMAGES, "start.png")
IM_STOP = os.path.join(PATH_IMAGES, "stop_m.png")

IM_ERROR_DATA = """
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
"""

IM_QUESTION_DATA = """
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
SUVORK5CYII=
"""

IM_INFO_DATA = """
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
9Uqvu3HLjfhvTUo85WzjhogAAAAASUVORK5CYII=
"""

IM_WARNING_DATA = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAABSZJREFU
WIXll1toVEcYgL+Zc87u2Yu7MYmrWRuTJuvdiMuqiJd4yYKXgMQKVkSjFR80kFIVJfWCWlvpg4h9
8sXGWGof8iKNICYSo6JgkCBEJRG8ImYThNrNxmaTeM7pQ5IlJkabi0/9YZhhZv7///4z/8zPgf+7
KCNRLgdlJijXwRyuDTlcxV9hbzv8nQmxMjg+XDtiOEplkG9PSfkztGmTgmFQd+FCVzwa3fYN/PHZ
AcpBaReicW5xcbb64IEQqko8Lc26d/58cxS+/BY6hmJvyEfQBoUpwWCmW1FErKaGWHU13uRk4QkE
UtxQNFR7QwIoB4eiKD9PWbVKbb10CZmaCqmpxCormRYO26QQx85B0mcD+AeK0xYvHqu1tNDx+DH6
gQM4jh0j3tCA3tGBLyfHLuD7zwJwAcYqun44sHy51nr5MsqsWWj5+djCYdS5c4ldvUr24sU2qarf
lUL6qAN0wqH0vDy7+fAhXZEI+v79CNmt7igpofPVK5SmJvyhkJBwYlQBSiHd7vUWZ86bp8WqqtCW
LkVbuBAhBEIItGAQ2+rVxG7cICMY1KTDsekc5IwagIQTmStXis47dzBiMfR9+xCi+wb39s79+zFi
MczGRjLmzTMlnBoVgLMwyzF+/Cb/lClq2/Xr2AoKUKdPxzAMWltbiUajmKaJkpGBY8sW3tbW4g8E
VNXrXVEKK0YMoMKp7Px8K15Tg2VZOHbvBiASiRAMBgkGg0QiEYQQOIuLsRSFrnv3yJo/HxVOW594
7D4KUAa57qysvNSUFOVtbS32rVuRfj9CCFwuV2Kfy+VCCIFMScFVVET7/fukJidLm883rQy+HhaA
BUII8cvUNWt4W1WFcLvRd+5MnHl/AOjOB+eOHchx44jX1ZEdCqkSTpaDbcgA5+GrpNmzc9ymKdvr
67Hv2oVMSko4cjgcKIqCoijoup64EdLpxLV3Lx1PnuCVUrgmTfK9hV1DAjgKqlSUk1PCYdl25QrS
70cvLEw4SWS+04nT6XxvXgiBc8MGtKlTaa+rIysnR1Ok/OF38PxngAzY4VuwYKL99WvR8fQpjj17
kLqeiL6393g8eDyeAWBSVfEcOkRXczOOaBRvVpZuDPJEDwD4DVyKrv+UlZurxSorUWfMQC8oGOBc
CDHgC/Rdc4TD2BctIl5fT+bkyTahaXvOw8RPApiwd2Ju7hjZ2EhXSwvOkhKQcoADgIqKCioqKgYc
QW9LOnIEIxZDbWpiXCCABT9+FKAUxtm83pKMUEiLVVejLVqEtmTJB50LIdi2bRuFPbnRd7232efM
wbVuHR2PHjHR77dJXS8sg5mDAihweFJenmrevYvR1oazpGTQ6IQQaJqG7ClI/dd655IOHsSyLMSL
F6QFAib9nugEQClk2Xy+orTsbK3t1i3sa9ei5eQMGr0QgvLyci5evDiocyEEtsxMPNu30/nsGRO8
XlVzu8NlkNvrV+0T/fHMZcusrtu3MeNx9PXrobUVq8cYQrw3TrRub1h9+v573Bs3Ej1zBvP5c/zp
6dbLhoaTwPy+ANKCfF92thq7dg2A6JYt/fNlxGK8eUNSerryHEJHQT8K8V4A5ztojty8OeaLzZul
1DSwLCzDANPEMozusWFgmWZ33288YK3/nGlixuM0v3xpWfDX0Z4i1VupXEWwIgRnJfhGPfQ+YsLr
+7DzNFwCuvqWyiRg7DSYoIBu9smPkYqEd4AwIN4ITUAL0A4Da7UC6ICdEfy2fUBMoAvo7GnWKNoe
mfwLcAuinuFNL7QAAAAASUVORK5CYII=
"""

ICONS = {"information": IM_INFO_DATA, "error": IM_ERROR_DATA,
         "question": IM_QUESTION_DATA, "warning": IM_WARNING_DATA}

# --- task state
TASK_STATE = {'Pending': '⌛', 'In Progress': '✎', 'Completed': '✔',
              'Cancelled': '✗'}

TASK_REV_TRANSLATION = {_(task): task for task in TASK_STATE}

# --- matplotlib config
matplotlib.rc("axes.formatter", use_locale=True)
matplotlib.rc('text', usetex=False)
matplotlib.rc('font', size=12)


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

if GUI == 'tk':
    ICON = TKTRAY_ICON
else:
    ICON = ICON_NAME

save_config()


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


# --- alternative filebrowser / colorchooser
ZENITY = False

tkfb = False
try:
    import tkfilebrowser as tkfb
except ImportError:
    tkfb = False
try:
    import tkcolorpicker as tkcp
except ImportError:
    tkcp = False

if os.name != "nt":
    paths = os.environ['PATH'].split(":")
    for path in paths:
        if os.path.exists(os.path.join(path, "zenity")):
            ZENITY = True


def askopenfilename(filetypes, initialdir, initialfile="", defaultextension="",
                    title=_('Open'), **options):
    """
    Plateform specific file browser.

    Arguments:
        - defaultextension: extension added if none is given
        - initialdir: directory where the filebrowser is opened
        - filetypes: [('NOM', '*.ext'), ...]
    """
    filetypes2 = [(name, exts.replace('|', ' ')) for name, exts in filetypes]
    if tkfb:
        return tkfb.askopenfilename(title=title,
                                    defaultext=defaultextension,
                                    filetypes=filetypes,
                                    initialdir=initialdir,
                                    initialfile=initialfile,
                                    **options)
    elif ZENITY:
        try:
            args = ["zenity", "--file-selection",
                    "--filename", os.path.join(initialdir, initialfile)]
            for ext in filetypes:
                args += ["--file-filter", "%s|%s" % ext]
            args += ["--title", title]
            file = check_output(args).decode("utf-8").strip()
            filename, ext = os.path.splitext(file)
            if not ext:
                ext = defaultextension
            return filename + ext
        except CalledProcessError:
            return ""
        except Exception:
            return filedialog.askopenfilename(title=title,
                                              defaultextension=defaultextension,
                                              filetypes=filetypes2,
                                              initialdir=initialdir,
                                              initialfile=initialfile,
                                              **options)
    else:
        return filedialog.askopenfilename(title=title,
                                          defaultextension=defaultextension,
                                          filetypes=filetypes2,
                                          initialdir=initialdir,
                                          initialfile=initialfile,
                                          **options)


def askcolor(color=None, **options):
    """
    Plateform specific color chooser.

    return the chose color in #rrggbb format.
    """
    if tkcp:
        color = tkcp.askcolor(color, **options)
        if color:
            return color[1]
        else:
            return None
    elif ZENITY:
        try:
            args = ["zenity", "--color-selection", "--show-palette"]
            if "title" in options:
                args += ["--title", options["title"]]
            if color:
                args += ["--color", color]
            color = check_output(args).decode("utf-8").strip()
            if color:
                if color[0] == "#":
                    if len(color) == 13:
                        color = "#%s%s%s" % (color[1:3], color[5:7], color[9:11])
                elif color[:4] == "rgba":
                    color = color[5:-1].split(",")
                    color = '#%02x%02x%02x' % (int(color[0]), int(color[1]), int(color[2]))
                elif color[:3] == "rgb":
                    color = color[4:-1].split(",")
                    color = '#%02x%02x%02x' % (int(color[0]), int(color[1]), int(color[2]))
                else:
                    raise TypeError("Color formatting not understood.")
            return color
        except CalledProcessError:
            return None
        except Exception:
            color = colorchooser.askcolor(color, **options)
            return color[1]
    else:
        color = colorchooser.askcolor(color, **options)
        return color[1]


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


def only_nb(text):
    return text == '' or text.isdigit()


def scrub(table_name):
    return ''.join(ch for ch in table_name if ch.isalnum() or ch == '_')
