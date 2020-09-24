#! /usr/bin/python3
# -*-coding:Utf-8 -*

"""
Scheduler - Task scheduling and calendar
Copyright 2015-2019 Juliette Monsel <j_4321@protonmail.com>

Scheduler is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Scheduler  is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Pomodoro widget
"""
import logging
import sqlite3
import datetime as dt
from subprocess import Popen
from tkinter import StringVar, Menu, IntVar
from tkinter.ttk import Button, Label, Frame, Menubutton, Sizegrip
from tkinter.messagebox import askyesno

from schedulerlib.pomodoro_stats import Stats
from schedulerlib.constants import CONFIG, CMAP, PATH_STATS, active_color, scrub
from .base_widget import BaseWidget


class Pomodoro(BaseWidget):
    """Pomodoro Timer widget."""
    def __init__(self, master):
        BaseWidget.__init__(self, 'Pomodoro', master)

    def create_content(self, **kw):
        """Create pomodoro timer's GUI."""
        self.minsize(190, 190)

        self.on = False  # is the timer on?

        if not CONFIG.options("Tasks"):
            CONFIG.set("Tasks", _("Work"), CMAP[0])

        self._stats = None

        # --- colors
        activities = ['work', 'rest', 'break']
        self.background = {_(act.capitalize()): CONFIG.get("Pomodoro", f"{act}_bg")
                           for act in activities}
        self.foreground = {_(act.capitalize()): CONFIG.get("Pomodoro", f"{act}_fg")
                           for act in activities}

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # nombre de séquence de travail effectuées d'affilée (pour
        # faire des pauses plus longues tous les 4 cycles)
        self.nb_cycles = 0
        self.pomodori = IntVar(self, 0)

        # --- tasks list
        tasks_frame = Frame(self, style='Pomodoro.TFrame')
        tasks_frame.grid(row=3, column=0, columnspan=3, sticky="wnse")
        tasks = [t.capitalize() for t in CONFIG.options("PomodoroTasks")]
        tasks.sort()
        self.task = StringVar(self, tasks[0])
        self.menu_tasks = Menu(tasks_frame, relief='sunken', activeborderwidth=0)
        self.choose_task = Menubutton(tasks_frame, textvariable=self.task,
                                      menu=self.menu_tasks, style='Pomodoro.TMenubutton')
        Label(tasks_frame,
              text=_("Task: "),
              style='Pomodoro.TLabel',
              font="TkDefaultFont 12",
              width=6,
              anchor="e").pack(side="left", padx=4)
        self.choose_task.pack(side="right", fill="x", pady=4)

        # --- display
        self.tps = [CONFIG.getint("Pomodoro", "work_time"), 0]  # time: min, sec
        self.activite = StringVar(self, _("Work"))
        self.titre = Label(self,
                           textvariable=self.activite,
                           font='TkDefaultFont 14',
                           style='timer.Pomodoro.TLabel',
                           anchor="center")
        self.titre.grid(row=0, column=0, columnspan=2, sticky="we", pady=(4, 0), padx=4)
        self.temps = Label(self,
                           text="{0:02}:{1:02}".format(self.tps[0], self.tps[1]),
                           style='timer.Pomodoro.TLabel',
                           anchor="center")
        self.temps.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=4)
        self.aff_pomodori = Label(self, textvariable=self.pomodori, anchor='e',
                                  padding=(20, 4, 20, 4),
                                  image='img_pomodoro', compound="left",
                                  style='timer.Pomodoro.TLabel',
                                  font='TkDefaultFont 14')
        self.aff_pomodori.grid(row=2, columnspan=2, sticky="ew", padx=4)

        # --- buttons
        self.b_go = Button(self, image='img_start', command=self.go,
                           style='Pomodoro.TButton')
        self.b_go.grid(row=4, column=0, sticky="ew")
        self.b_stats = Button(self, image='img_graph',
                              command=self.display_stats,
                              style='Pomodoro.TButton')
        self.b_stats.grid(row=4, column=1, sticky="ew")

        self._corner = Sizegrip(self, style="Pomodoro.TSizegrip")
        self._corner.place(relx=1, rely=1, anchor='se')

        # --- bindings
        self.bind('<3>', lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        tasks_frame.bind('<ButtonPress-1>', self._start_move)
        tasks_frame.bind('<ButtonRelease-1>', self._stop_move)
        tasks_frame.bind('<B1-Motion>', self._move)
        self.titre.bind('<ButtonPress-1>', self._start_move)
        self.titre.bind('<ButtonRelease-1>', self._stop_move)
        self.titre.bind('<B1-Motion>', self._move)
        self.temps.bind('<ButtonPress-1>', self._start_move)
        self.temps.bind('<ButtonRelease-1>', self._stop_move)
        self.temps.bind('<B1-Motion>', self._move)
        self.b_stats.bind('<Enter>', self._on_enter)
        self.b_stats.bind('<Leave>', self._on_leave)

    def update_style(self):
        """Update widget's style."""
        BaseWidget.update_style(self)
        self.menu_tasks.delete(0, 'end')
        tasks = [t.capitalize() for t in CONFIG.options('PomodoroTasks')]
        tasks.sort()
        for task in tasks:
            self.menu_tasks.add_radiobutton(label=task, value=task,
                                            variable=self.task)
        if self.task.get() not in tasks:
            self.stop(False)
            self.task.set(tasks[0])

        bg = CONFIG.get('Pomodoro', 'background')
        fg = CONFIG.get('Pomodoro', 'foreground')
        active_bg = active_color(*self.winfo_rgb(bg))

        self.menu_tasks.configure(bg=bg, activebackground=active_bg, fg=fg,
                                  selectcolor=fg, activeforeground=fg)
        activities = ['work', 'rest', 'break']
        self.background = {_(act.capitalize()): CONFIG.get("Pomodoro", f"{act}_bg")
                           for act in activities}
        self.foreground = {_(act.capitalize()): CONFIG.get("Pomodoro", f"{act}_fg")
                           for act in activities}
        act = self.activite.get()
        self.style.configure('timer.Pomodoro.TLabel',
                             font=CONFIG.get("Pomodoro", "font"),
                             foreground=self.foreground[act],
                             background=self.background[act])

    # --- widget resizing and visibility
    def _on_enter(self, event=None):
        self._corner.state(('active',))

    def _on_leave(self, event=None):
        self._corner.state(('!active',))

    def hide(self):
        if self._stats is not None:
            self._stats.destroy()
        BaseWidget.hide(self)

    # --- widget specific methods
    def stats(self, time=None):
        """Save stats."""
        if time is None:
            time = CONFIG.getint("Pomodoro", "work_time")
        today = dt.date.today().toordinal()
        task = self.task.get().lower().replace(' ', '_')
        db = sqlite3.connect(PATH_STATS)
        cursor = db.cursor()
        try:
            cursor.execute('SELECT * FROM {} ORDER BY id DESC LIMIT 1'.format(scrub(task)))
            key, date, work = cursor.fetchone()
        except sqlite3.OperationalError:
            cursor.execute('''CREATE TABLE {} (id INTEGER PRIMARY KEY,
                                               date INTEGER,
                                               work INTEGER)'''.format(scrub(task)))
            cursor.execute('INSERT INTO {}(date, work) VALUES (?, ?)'.format(scrub(task)),
                           (today, time))
        else:
            if today != date:
                cursor.execute('INSERT INTO {}(date, work) VALUES (?, ?)'.format(scrub(task)),
                               (today, time))
            else:  # update day's value
                cursor.execute('UPDATE {} SET work=? WHERE id=?'.format(scrub(task)), (work + time, key))
        finally:
            db.commit()
            db.close()

    def display_stats(self):
        """ affiche les statistiques """
        if self._stats is None:
            self._stats = Stats(self)
            self._stats.bind('<Destroy>', self._on_close_stats)
        else:
            self._stats.lift()

    def _on_close_stats(self, event):
        self._stats = None

    def go(self):
        if self.on:
            self.stop()
        else:
            self.on = True
            self.choose_task.state(["disabled"])
            self.b_go.configure(image='img_stop')
            self.after(1000, self.affiche)
            logging.info('Start work cycle for task ' + self.task.get())

    def stop(self, confirmation=True):
        """ Arrête le décompte du temps et le réinitialise,
            demande une confirmation avant de le faire si confirmation=True """
        tps = int(CONFIG.getint("Pomodoro", "work_time") - self.tps[0] - self.tps[1] / 60)
        self.on = False
        rep = True
        if confirmation:
            rep = askyesno(title=_("Confirmation"),
                           message=_("Are you sure you want to give up the current session?"))
        if rep:
            self.choose_task.state(["!disabled"])
            self.b_go.configure(image='img_start')
            if self.activite.get() == _("Work"):
                self.stats(tps)
            self.pomodori.set(0)
            self.nb_cycles = 0
            self.tps = [CONFIG.getint("Pomodoro", "work_time"), 0]
            self.temps.configure(text="{0:02}:{1:02}".format(self.tps[0], self.tps[1]))
            act = _("Work")
            self.activite.set(act)
            self.style.configure('timer.Pomodoro.TLabel',
                                 background=self.background[act],
                                 foreground=self.foreground[act])
            logging.info('Pomodoro session interrupted.')
        else:
            self.on = True
            self.affiche()
        return rep

    @staticmethod
    def ting():
        """Play the sound notifying the end of a period."""
        if (not CONFIG.getboolean("Pomodoro", "mute") and
                not CONFIG.getboolean('General', 'silent_mode')):
            Popen([CONFIG.get("General", "soundplayer"),
                   CONFIG.get("Pomodoro", "beep")])

    def affiche(self):
        if self.on:
            self.tps[1] -= 1
            if self.tps[1] == 0:
                if self.tps[0] == 0:
                    self.ting()
                    if self.activite.get() == _("Work"):
                        self.pomodori.set(self.pomodori.get() + 1)
                        self.nb_cycles += 1
                        self.choose_task.state(["!disabled"])
                        logging.info('Pomodoro: completed work session for task ' + self.task.get())
                        if self.nb_cycles % 4 == 0:
                            # pause longue
                            self.stats()
                            self.activite.set(_("Rest"))
                            self.tps = [CONFIG.getint("Pomodoro", "rest_time"), 0]
                        else:
                            # pause courte
                            self.stats()
                            self.activite.set(_("Break"))
                            self.tps = [CONFIG.getint("Pomodoro", "break_time"), 0]
                    else:
                        self.choose_task.state(["disabled"])
                        self.activite.set(_("Work"))
                        self.tps = [CONFIG.getint("Pomodoro", "work_time"), 0]
                    act = self.activite.get()
                    self.style.configure('timer.Pomodoro.TLabel',
                                         background=self.background[act],
                                         foreground=self.foreground[act])
            elif self.tps[1] == -1:
                self.tps[0] -= 1
                self.tps[1] = 59
            self.temps.configure(text="{0:02}:{1:02}".format(*self.tps))
            self.after(1000, self.affiche)

