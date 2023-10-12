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


Constants and functions.
"""
import os
import locale
import logging
from logging.handlers import TimedRotatingFileHandler
from configparser import ConfigParser
import warnings
import gettext
from subprocess import check_output, CalledProcessError
from tkinter import filedialog
from tkinter import colorchooser

from babel import dates
from dateutil import relativedelta


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
    ICON_NOTIF = os.path.join(PATH_IMAGES, "scheduler-tray.svg")
else:
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.expanduser('~'), '.scheduler')
    PATH_LOCALE = "/usr/share/locale"
    PATH_IMAGES = "/usr/share/scheduler/images"
    PATH_SOUNDS = "/usr/share/scheduler/sounds"
    ICON_NOTIF = "scheduler"

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
OPENFILE_PATH = os.path.join(LOCAL_PATH, ".file")

if not os.path.exists(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)

if not os.path.exists(os.path.dirname(BACKUP_PATH)):
    os.mkdir(os.path.dirname(BACKUP_PATH))

# --- stat colors
CMAP = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#17becf', '#ff00ff', '#7f7f7f', '#bcbd22', '#9467bd']

# --- log
handler = TimedRotatingFileHandler(LOG_PATH, when='midnight', backupCount=7)
logging.basicConfig(level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[handler])
logging.getLogger().addHandler(logging.StreamHandler())

# --- config
CONFIG = ConfigParser(interpolation=None)


def save_config():
    CONFIG.set('Calendar', 'holidays', ', '.join(HOLIDAYS))
    with open(CONFIG_PATH, 'w') as file:
        CONFIG.write(file)


default_config = {
    'General': {
        'locale': locale.getdefaultlocale()[0],
        'backups': '10',
        'trayicon': '',
        'language': "",
        'splash_supported': str(os.environ.get('DESKTOP_SESSION') != 'plasma'),
        'soundplayer': "mpg123",
        'silent_mode': "False",
    },
    'Eyes': {
        'interval': "20",
        'sound': os.path.join(PATH_SOUNDS, 'ting.mp3'),
        'mute': 'False',
    },
    'Reminders': {
        'window': 'True',
        'window_alpha': '0.75',
        'window_bg': 'gray10',
        'window_fg': 'white',
        'window_bg_alternate': 'gray30',
        'window_fg_alternate': 'red',
        'notification': 'True',
        'mute': 'True',
        'alarm': os.path.join(PATH_SOUNDS, 'alarm.mp3'),
        'blink': 'True',
        'timeout': '5',
    },
    'Events': {
        'geometry': '',
        'visible': 'True',
        'alpha': '0.85',
        'font': 'Liberation\ Sans 10',
        'font_title': 'Liberation\ Sans 12 bold',
        'font_day': 'Liberation\ Sans 11 bold',
        'foreground': 'white',
        'background': 'gray10',
        'position': 'normal',
    },
    'Tasks': {
        'geometry': '',
        'visible': 'True',
        'alpha': '0.85',
        'font': 'Liberation\ Sans 10',
        'font_title': 'Liberation\ Sans 12 bold',
        'foreground': 'white',
        'background': 'gray10',
        'position': 'normal',
        'hide_completed': 'False',
    },
    'Timer': {
        'geometry': '',
        'visible': 'True',
        'alpha': '0.85',
        'font': 'Liberation\ Sans 10',
        'font_time': 'FreeMono 26',
        'font_intervals': 'FreeMono 12',
        'foreground': 'white',
        'background': 'gray10',
        'position': 'normal',
    },
    'Calendar': {
        'holidays': '',
        'geometry': '',
        'visible': 'True',
        'alpha': '0.85',
        'font': 'TkDefaultFont 8',
        'background': '#424242',
        'foreground': '#ECECEC',
        'bordercolor': 'gray70',
        'othermonthforeground': 'gray30',
        'othermonthbackground': 'gray93',
        'othermonthweforeground': 'gray30',
        'othermonthwebackground': 'gray75',
        'normalforeground': 'black',
        'normalbackground': 'white',
        'selectforeground': 'white',
        'selectbackground': '#424242',
        'weekendforeground': '#424242',
        'weekendbackground': 'lightgrey',
        'headersforeground': 'black',
        'headersbackground': 'gray70',
        'tooltipforeground': 'white',
        'tooltipbackground': 'black',
        'position': 'normal',
        'default_category': '',
    },
    'Categories': {}, # name: "fg, bg, order"
    'ExternalSync': {
        'frequency': "30",
        'calendars': ''
    },
    'ExternalCalendars': {},  # name (-> ExtCal property of the event): url_to_ics_file [one way sync remote -> local]
    'Pomodoro': {
        'geometry': '',
        'visible': 'True',
        'alpha': '0.85',
        'foreground': 'white',
        'background': 'gray10',
        'position': 'normal',
        'font': "FreeMono 48",
        'work_time': "25",
        'work_bg': "#ffffff",
        'work_fg': "#000000",
        'break_time': "5",
        'break_bg': "#77ABE2",
        'break_fg': "#000000",
        'rest_time': "20",
        'rest_bg': "#FF7A40",
        'rest_fg': "#000000",
        'beep': os.path.join(PATH_SOUNDS, 'ting.mp3'),
        'mute': "False",
        'legend_max_height': "6",
    },
    'PomodoroTasks': {}
}

for section, opts in default_config.items():
    CONFIG.setdefault(section, opts)

# restore config
if CONFIG.read(PATH_CONFIG):
    os.rename(PATH_CONFIG, PATH_CONFIG + '.bak')

if not CONFIG.options('Categories'):
    CONFIG.set('Categories', 'default', 'white, #186CBE, 0')

if not CONFIG.has_option('Events', 'categories'):
    CONFIG.set('Events', 'categories', ', '.join(CONFIG.options('Categories')))

if not CONFIG.get('Calendar', 'default_category'):
    CONFIG.set('Calendar', 'default_category', CONFIG.options('Categories')[0])
# --- language
LANGUAGE = CONFIG.get('General', 'language')

LANGUAGES = {"fr": "Français", "en": "English"}
REV_LANGUAGES = {val: key for key, val in LANGUAGES.items()}

if LANGUAGE not in LANGUAGES:
    # Check the default locale
    try:
        LANGUAGE = locale.getdefaultlocale()[0].split('_')[0]
    except Exception:
        LANGUAGE = "en"
    if LANGUAGE in LANGUAGES:
        CONFIG.set("General", "language", LANGUAGE)
    else:
        CONFIG.set("General", "language", "en")


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

save_config()


# change babel formatting default arguments
def format_date(date=None, format="short", locale=CONFIG.get("General", "locale")):
    return dates.format_date(date, format, locale)


def format_datetime(datetime=None, format='short', tzinfo=None,
                    locale=CONFIG.get("General", "locale")):
    return dates.format_datetime(datetime, format, tzinfo, locale)


def format_time(time=None, format='short', tzinfo=None,
                locale=CONFIG.get("General", "locale")):
    return dates.format_time(time, format, tzinfo, locale)


# set locale for pomodoro stats display
try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    # on some platforms there are issues with the default locale format
    pass

# --- images
ICON_NAME = "scheduler-tray"  # gtk / qt tray icon
ICON_FALLBACK = os.path.join(PATH_IMAGES, "scheduler-tray.svg")  # gtk / qt fallback tray icon
TKTRAY_ICON = os.path.join(PATH_IMAGES, 'scheduler.png')
IM_SCROLL_ALPHA = os.path.join(PATH_IMAGES, "scroll.png")
IM_EYE = os.path.join(PATH_IMAGES, "eye.svg")

IMAGES = {}
for img in os.listdir(PATH_IMAGES):
    name, ext = os.path.splitext(img)
    if ext == '.png':
        IMAGES[name] = os.path.join(PATH_IMAGES, img)

ICONS = ['warning', 'information', 'question', 'error']

# --- task state
TASK_STATE = {'Pending': '⌛', 'In Progress': '✎', 'Completed': '✔',
              'Cancelled': '✗'}

TASK_REV_TRANSLATION = {_(task): task for task in TASK_STATE}


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
GUI = CONFIG.get("General", "trayicon").lower()

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


def asksaveasfilename(defaultextension, filetypes, initialdir=".", initialfile="",
                      title=_('Save As'), **options):
    """
    Open filebrowser dialog to select file to save to.

    Arguments:
        - defaultextension: extension added if none is given
        - initialdir: directory where the filebrowser is opened
        - initialfile: initially selected file
        - filetypes: [('NAME', '*.ext'), ...]
    """
    if tkfb:
        return tkfb.asksaveasfilename(title=title,
                                      defaultext=defaultextension,
                                      filetypes=filetypes,
                                      initialdir=initialdir,
                                      initialfile=initialfile,
                                      **options)
    elif ZENITY:
        try:
            args = ["zenity", "--file-selection",
                    "--filename", os.path.join(initialdir, initialfile),
                    "--save", "--confirm-overwrite"]
            for ext in filetypes:
                args += ["--file-filter", "%s|%s" % ext]
            args += ["--title", title]
            file = check_output(args).decode("utf-8").strip()
            if file:
                filename, ext = os.path.splitext(file)
                if not ext:
                    ext = defaultextension
                return filename + ext
            else:
                return ""
        except CalledProcessError:
            return ""
        except Exception:
            return filedialog.asksaveasfilename(title=title,
                                                defaultextension=defaultextension,
                                                initialdir=initialdir,
                                                filetypes=filetypes,
                                                initialfile=initialfile,
                                                **options)
    else:
        return filedialog.asksaveasfilename(title=title,
                                            defaultextension=defaultextension,
                                            initialdir=initialdir,
                                            filetypes=filetypes,
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


def active_color(R, G, B, output='HTML'):
    """Return a lighter shade of color (RGB triplet with value max 255) in HTML format."""
    coef = 255 / 65535
    r, g, b = R * coef, G * coef, B * coef
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
        return (round(r) / coef, round(g) / coef, round(b) / coef)


def only_nb(text):
    return text == '' or text.isdigit()


def scrub(table_name):
    return ''.join(ch for ch in table_name if ch.isalnum() or ch == '_')


def get_rel_month_day(date):
    """
    Return (week day number, relative month day nb) for date.

    For instance, returns (0, 1) for the first Monday of the month and
    (6, -1) for the last Sunday.
    """
    wd = date.weekday()
    last = date + relativedelta.relativedelta(day=31,
                                              weekday=relativedelta.weekday(wd)(-1)) # last wday of the month
    if last == date:
        return wd, -1
    else:
        first = date + relativedelta.relativedelta(day=1,
                                                   weekday=relativedelta.weekday(wd)(1))  # first wday of the month
        return wd, date.isocalendar()[1] - first.isocalendar()[1] + 1
