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


main
"""
import os
import sys
import logging
import argparse
import signal
from tkinter import Tk
from tkinter.messagebox import showerror

from schedulerlib.constants import PIDFILE, save_config


# parse command line arguments
parser = argparse.ArgumentParser(description=_("Scheduler - Task scheduling and calendar"),
                                 epilog=_("Report bugs to https://github.com/j4321/Scheduler/issues."))
parser.add_argument('-V', '--version', help=_('show version and exit'),
                    action='store_true')
parser.add_argument('-U', '--update-date',
                    help=_('if scheduler is running, update selected date in calendar (done automatically every day at 00:00:01)'),
                    action='store_true')
parser.add_argument('-W', '--withdraw',
                    help=_('start scheduler without displaying the manager window'),
                    action='store_true')
args = parser.parse_args()

if args.version:
    from schedulerlib.version import __version__
    print('scheduler ' + __version__)
    sys.exit()


# check wether scheduler is already running
pid = str(os.getpid())

if os.path.isfile(PIDFILE):
    with open(PIDFILE) as fich:
        old_pid = fich.read().strip()
    if os.path.exists("/proc/%s" % old_pid):
        with open("/proc/%s/cmdline" % old_pid) as file:
            cmdline = file.read()
        if 'scheduler' in cmdline:
            if args.update_date:
                # send signal to scheduler to update the selected date
                os.kill(int(old_pid), signal.SIGUSR1)
                sys.exit()
            else:
                # already runnning
                root = Tk()
                root.withdraw()
                showerror(_("Error"),
                          _("Scheduler is already running. If not deletes {pidfile}.").format(pidfile=PIDFILE))
                sys.exit()
    # it is an old pid file (certainly due to session logout then login)
    os.remove(PIDFILE)

if args.update_date:
    # scheduler was not running, does nothing
    sys.exit()

open(PIDFILE, 'w').write(pid)

try:
    from schedulerlib.scheduler import EventScheduler

    app = EventScheduler()
    if not args.withdraw:
        app.show()
    app.mainloop()
finally:
    try:
        app.save()
    except NameError:
        pass
    save_config()
    try:
        os.unlink(PIDFILE)
    except FileNotFoundError:
        # PIDFILE might have been deleted
        pass
    logging.info('Quit')
