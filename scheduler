#!/usr/bin/python3
# -*- coding: utf-8 -*-

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
                      _("Scheduler is already running. If not deletes {pidfile}").format(pidfile=PIDFILE))
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
