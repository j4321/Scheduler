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
PATH_STATS = os.path.join(LOCAL_PATH, "pomodoro_stats")
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

if not os.path.exists(PATH_STATS):
    os.mkdir(PATH_STATS)

# --- stat colors
CMAP = ["blue", "green", "red", "cyan", "magenta", "yellow", "white", "black"]

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
    CONFIG.set("Pomodoro", "player", "")
    CONFIG.set("Pomodoro", "mute", "False")

    CONFIG.add_section("PomodoroTasks")


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


# --- retrieve holidays
HOLIDAYS = set(CONFIG.get('Calendar', 'holidays').split(', '))
if '' in HOLIDAYS:
    HOLIDAYS.remove('')

# --- default pomodoro task
if not CONFIG.options("PomodoroTasks"):
    # task = color
    CONFIG.set("PomodoroTasks", _("Work"), CMAP[0])

# --- default sound player
if not CONFIG.get("Pomodoro", "player"):
    if os.path.exists("/usr/bin/aplay"):
        CONFIG.set("Pomodoro", "player", "aplay")
    elif os.path.exists("/usr/bin/paplay"):
        CONFIG.set("Pomodoro", "player", "paplay")
    elif os.path.exists("/usr/bin/mpg123"):
        CONFIG.set("Pomodoro", "player", "mpg123")
    elif os.path.exists("/usr/bin/cvlc"):
        CONFIG.set("Pomodoro", "player", "cvlc")
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
            CONFIG.set("Pomodoro", "player", player.get())
            top.destroy()

        Button(top, _("Cancel"), command=top.destroy).grid(row=2, column=0)
        Button(top, _("Ok"), command=valide).grid(row=2, column=1)


# --- images
ICON_NAME = "scheduler-tray"  # gtk / qt tray icon
ICON48 = os.path.join(PATH_IMAGES, 'icon48.png')
TKTRAY_ICON = os.path.join(PATH_IMAGES, 'scheduler.png')
BELL = os.path.join(PATH_IMAGES, 'bell.png')
MOINS = os.path.join(PATH_IMAGES, 'moins.png')
PLUS = os.path.join(PATH_IMAGES, 'plus.png')
DOT = os.path.join(PATH_IMAGES, 'dot.png')
PLAY = os.path.join(PATH_IMAGES, 'play.png')
PAUSE = os.path.join(PATH_IMAGES, 'pause.png')
STOP = os.path.join(PATH_IMAGES, 'stop.png')
TOMATE = os.path.join(PATH_IMAGES, "tomate.png")
GRAPH = os.path.join(PATH_IMAGES, "graph.png")
PARAMS = os.path.join(PATH_IMAGES, "params.png")
COLOR = os.path.join(PATH_IMAGES, "color.png")
SON = os.path.join(PATH_IMAGES, "son.png")
MUTE = os.path.join(PATH_IMAGES, "mute.png")
CLOSED = os.path.join(PATH_IMAGES, 'closed.png')
OPENED = os.path.join(PATH_IMAGES, 'open.png')
CLOSED_SEL = os.path.join(PATH_IMAGES, 'closed_sel.png')
OPENED_SEL = os.path.join(PATH_IMAGES, 'open_sel.png')
SCROLL_ALPHA = os.path.join(PATH_IMAGES, "scroll.png")


TASK_STATE = {'Pending': '⌛', 'In Progress': '✎', 'Completed': '✔', 'Cancelled': '✗'}


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


def valide_entree_nb(d, S):
    """ commande de validation des champs devant contenir
        seulement des chiffres """
    if d == '1':
        return S.isdigit()
    else:
        return True
