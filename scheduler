#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Scheduler - Task scheduling and calendar
Copyright 2017-2018 Juliette Monsel <j_4321@protonmail.com>

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

from schedulerlib.scheduler import EventScheduler
from schedulerlib.constants import PIDFILE, save_config
import os
import sys
import logging
from tkinter import Tk
from tkinter.messagebox import showerror

# vérifie si mynotes est déjà lancé
pid = str(os.getpid())

if os.path.isfile(PIDFILE):
    with open(PIDFILE) as fich:
        old_pid = fich.read().strip()
    if os.path.exists("/proc/%s" % old_pid):
        with open("/proc/%s/cmdline" % old_pid) as file:
            cmdline = file.read()
        if 'scheduler' in cmdline:
            # already runnning
            root = Tk()
            root.withdraw()
            showerror(_("Error"),
                      _("Scheduler is already running. If not deletes {pidfile}.").format(pidfile=PIDFILE))
            sys.exit()
    # it is an old pid file (certainly due to session logout then login)
    os.remove(PIDFILE)

open(PIDFILE, 'w').write(pid)

try:
    app = EventScheduler()
    if '--withdraw' not in sys.argv:
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
