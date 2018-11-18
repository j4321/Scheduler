#! /usr/bin/python3
# -*-coding:Utf-8 -*

"""
WorkHourGlass - Enhance your efficiency by timing your work and breaks
Copyright 2015-2018 Juliette Monsel <j_4321@protonmail.com>

WorkHourGlass is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

WorkHourGlass  is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Pomodoro GUI
"""
from subprocess import Popen
from tkinter import StringVar, Menu, IntVar, PhotoImage
from tkinter.ttk import Button, Label, Frame, Menubutton, Sizegrip
from tkinter.messagebox import askyesno
import os
import matplotlib.pyplot as plt
from numpy import zeros, zeros_like, array, arange, concatenate, loadtxt
import datetime as dt
from schedulerlib.constants import CONFIG, CMAP, PATH_STATS, PLAY, \
    STOP, TOMATE, PARAMS, GRAPH, active_color
from .base_widget import BaseWidget

# TODO: fix task deletion


class Pomodoro(BaseWidget):
    """ Chronometre de temps de travail pour plus d'efficacité """
    def __init__(self, master):
        BaseWidget.__init__(self, 'Pomodoro', master)
        self.minsize(190, 190)

        self.on = False  # is the timer on?

        if not CONFIG.options("Tasks"):
            CONFIG.set("Tasks", _("Work"), CMAP[0])

        # --- colors
        self.background = {_("Work"): CONFIG.get("Pomodoro", "work_bg"),
                           _("Break"): CONFIG.get("Pomodoro", "break_bg"),
                           _("Rest"): CONFIG.get("Pomodoro", "rest_bg")}
        self.foreground = {_("Work"): CONFIG.get("Pomodoro", "work_fg"),
                           _("Break"): CONFIG.get("Pomodoro", "break_fg"),
                           _("Rest"): CONFIG.get("Pomodoro", "rest_fg")}

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # nombre de séquence de travail effectuées d'affilée (pour
        # faire des pauses plus longues tous les 4 cycles)
        self.nb_cycles = 0
        self.pomodori = IntVar(self, 0)

        # --- images
        self.im_go = PhotoImage(master=self, file=PLAY)
        self.im_stop = PhotoImage(master=self, file=STOP)
        self.im_params = PhotoImage(master=self, file=PARAMS)
        self.im_tomate = PhotoImage(master=self, file=TOMATE)
        self.im_graph = PhotoImage(master=self, file=GRAPH)

        # --- tasks list
        tasks_frame = Frame(self, style='pomodoro.TFrame')
        tasks_frame.grid(row=3, column=0, columnspan=3, sticky="wnse")
        tasks = [t.capitalize() for t in CONFIG.options("PomodoroTasks")]
        self.task = StringVar(self, tasks[0])
        self.menu_tasks = Menu(tasks_frame, tearoff=False)
        self.choose_task = Menubutton(tasks_frame, textvariable=self.task,
                                      menu=self.menu_tasks, style='pomodoro.TMenubutton')
        Label(tasks_frame,
              text=_("Task: "),
              style='pomodoro.TLabel',
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
                           style='timer.pomodoro.TLabel',
                           anchor="center")
        self.titre.grid(row=0, column=0, columnspan=2, sticky="we", pady=(4, 0), padx=4)
        self.temps = Label(self,
                           text="{0:02}:{1:02}".format(self.tps[0], self.tps[1]),
                           style='timer.pomodoro.TLabel',
                           anchor="center")
        self.temps.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=4)
        self.aff_pomodori = Label(self, textvariable=self.pomodori, anchor='e',
                                  padding=(20, 4, 20, 4),
                                  image=self.im_tomate, compound="left",
                                  style='timer.pomodoro.TLabel',
                                  font='TkDefaultFont 14')
        self.aff_pomodori.grid(row=2, columnspan=2, sticky="ew", padx=4)

        # --- buttons
        self.b_go = Button(self, image=self.im_go, command=self.go,
                           style='pomodoro.TButton')
        self.b_go.grid(row=4, column=0, sticky="ew")
        self.b_stats = Button(self, image=self.im_graph,
                              command=self.display_stats,
                              style='pomodoro.TButton')
        self.b_stats.grid(row=4, column=1, sticky="ew")

        self._corner = Sizegrip(self, style="pomodoro.TSizegrip")
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
        self.menu_tasks.delete(0, 'end')
        tasks = [t.capitalize() for t in CONFIG.options('PomodoroTasks')]
        for task in tasks:
            self.menu_tasks.add_radiobutton(label=task, value=task,
                                            variable=self.task)
        if self.task.get() not in tasks:
            self.stop(False)
            self.task.set(tasks[0])

        self.attributes('-alpha', CONFIG.get(self.name, 'alpha', fallback=0.85))
        bg = CONFIG.get('Pomodoro', 'background')
        fg = CONFIG.get('Pomodoro', 'foreground')
        r, g, b = self.winfo_rgb(bg)
        active_bg = active_color(r * 255 / 65535, g * 255 / 65535, b * 255 / 65535)
        self.style.configure('pomodoro.TMenubutton', background=bg, relief='flat',
                             foreground=fg, borderwidth=0, arrowcolor=fg)
        self.style.configure('pomodoro.TButton', background=bg, relief='flat',
                             foreground=fg, borderwidth=0)
        self.style.configure('pomodoro.TLabel', background=bg,
                             foreground=fg)
        self.style.configure('pomodoro.TFrame', background=bg)
        self.style.configure('pomodoro.TSizegrip', background=bg)
        self.style.map('pomodoro.TSizegrip', background=[('active', active_bg)])
        self.style.map('pomodoro.TButton', background=[('disabled', bg),
                                                       ('!disabled', 'active', active_bg)])
        self.style.map('pomodoro.TMenubutton', background=[('disabled', bg),
                                                           ('!disabled', 'active', active_bg)])
        self.configure(bg=bg)
        self.background = {_("Work"): CONFIG.get("Pomodoro", "work_bg"),
                           _("Break"): CONFIG.get("Pomodoro", "break_bg"),
                           _("Rest"): CONFIG.get("Pomodoro", "rest_bg")}
        self.foreground = {_("Work"): CONFIG.get("Pomodoro", "work_fg"),
                           _("Break"): CONFIG.get("Pomodoro", "break_fg"),
                           _("Rest"): CONFIG.get("Pomodoro", "rest_fg")}
        act = self.activite.get()
        self.style.configure('timer.pomodoro.TLabel',
                             font=CONFIG.get("Pomodoro", "font"),
                             foreground=self.foreground[act],
                             background=self.background[act])

    def _on_enter(self, event=None):
        self._corner.state(('active',))

    def _on_leave(self, event=None):
        self._corner.state(('!active',))

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _stop_move(self, event):
        self.x = None
        self.y = None
        self.configure(cursor='arrow')

    def _move(self, event):
        if self.x is not None and self.y is not None:
            self.configure(cursor='fleur')
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry("+%s+%s" % (x, y))

    def hide(self):
        self.stats()
        plt.close()
        BaseWidget.hide(self)

    def stats(self):
        """ Enregistre la durée de travail (en min) effectuée ce jour pour la
            tâche qui vient d'être interrompue.
            Seul les pomodori complets sont pris en compte. """
        # TODO: translate, correct date/time format
        pom = self.pomodori.get()
        if pom:
            # la tâche en cours a été travaillée, il faut enregistrer les stats
            date = dt.date.today()
            task = self.task.get()
            chemin = os.path.join(PATH_STATS, "_".join(task.split(" ")))
            if not os.path.exists(chemin):
                with open(chemin, 'w') as fich:
                    fich.write("# tâche : %s\n# jour\tmois\tannée\ttemps de travail (min)\n" % task)
            with open(chemin, 'r') as fich:
                stats = fich.readlines()
            if len(stats) > 2:
                last = stats[-1][:10], stats[-1][:-1].split("\t")[-1]
            else:
                last = "", 0
            if last[0] != date.strftime("%d\t%m\t%Y"):
                with open(chemin, 'a') as fich:
                    fich.write("%s\t%i\n" % (date.strftime("%d\t%m\t%Y"),
                                             pom * CONFIG.getint("Pomodoro", "work_time")))
            else:
                # un nombre a déjà été enregistré plus tôt dans la journée
                # il faut les additioner
                with open(chemin, 'w') as fich:
                    fich.writelines(stats[:-1])
                    fich.write("%s\t%i\n" % (date.strftime("%d\t%m\t%Y"),
                                             pom * CONFIG.getint("Pomodoro", "work_time") + int(last[1])))

    def display_stats(self):
        """ affiche les statistiques """
        plt.figure("Statistiques")
        tasks = [t.capitalize() for t in CONFIG.options("PomodoroTasks")]
        coul = [CONFIG.get("PomodoroTasks", task) for task in tasks]
        stats_x = []
        stats_y = []

        demain = dt.date.today().toordinal() + 1
        min_x = demain

        # récupération des données
        no_data = True
        for i, task in enumerate(tasks):
            chemin = os.path.join(PATH_STATS, "_".join(task.split(" ")))
            if os.path.exists(chemin):
                no_data = False
                stat = loadtxt(chemin, dtype=int)
                if len(stat.shape) == 1:
                    stat = stat.reshape(1, 4)
                x = [dt.date(an, mois, jour).toordinal() for jour, mois, an in stat[:, :3]]
                y = stat[:, -1] / 60  # temps de travail
                min_x = min(x[0], min_x)
                stats_x.append(x)
                stats_y.append(y)
            else:
                # la taĉhe n'a jamais été travaillée
                stats_x.append([demain - 1])
                stats_y.append(array([0]))

        # plots
        xx = arange(min_x, demain, dtype=float)
        yy0 = zeros_like(xx)  # pour empiler les stats
        if not no_data:
            for (i, task), x, y in zip(enumerate(tasks), stats_x, stats_y):
                ax0 = plt.subplot(111)
                plt.ylabel(_("time (h)"))
                plt.xlabel(_("date"))
                yy = array([], dtype=int)
                # comble les trous par des 0
                # ainsi, les jours où une tâche n'a pas été travaillée correspondent
                # à des 0 sur le graph
                xxx = arange(min_x, x[0])
                yy = concatenate((yy, zeros_like(xxx, dtype=int)))
                for j in range(len(x) - 1):
                    xxx = arange(x[j], x[j + 1])
                    yy = concatenate((yy, [y[j]], zeros(len(xxx) - 1, dtype=int)))
                xxx = arange(x[-1], demain)
                yy = concatenate((yy, [y[-1]], zeros(len(xxx) - 1, dtype=int)))
                plt.bar(xx - 0.4, yy, bottom=yy0, width=0.8, label=task, color=coul[i])
                yy0 += yy
            axx = array([int(xt) for xt in ax0.get_xticks() if xt.is_integer()])
            ax0.set_xticks(axx)
            ax0.set_xticklabels([dt.date.fromordinal(i).strftime("%x") for i in axx])
            plt.gcf().autofmt_xdate()
            ax0.set_xlim(min_x - 0.5, demain - 0.5)
            lgd = plt.legend(fontsize=10)
            lgd.draggable()
            plt.subplots_adjust(top=0.95)
            max_y = yy0.max()
            ax0.set_ylim(0, max_y + 0.1 * max_y)
        plt.show()

    def go(self):
        if self.on:
            self.on = False
            self.b_go.configure(image=self.im_go)
            if self.activite.get() == _("Work"):
                self.stop()
        else:
            self.on = True
            self.choose_task.config(state="disabled")
            self.b_go.configure(image=self.im_stop)
            self.after(1000, self.affiche)

    def stop(self, confirmation=True):
        """ Arrête le décompte du temps et le réinitialise,
            demande une confirmation avant de le faire si confirmation=True """
        self.on = False
        if confirmation:
            rep = askyesno(title=_("Confirmation"),
                           message=_("Are you sure you want to give up the current session?"))
        else:
            rep = True
        if rep:
            self.stats()
            self.pomodori.set(0)
            self.nb_cycles = 0
            self.tps = [CONFIG.getint("Pomodoro", "work_time"), 0]
            self.temps.configure(text="{0:02}:{1:02}".format(self.tps[0], self.tps[1]))
            act = _("Work")
            self.activite.set(act)
            self.style.configure('timer.pomodoro.TLabel',
                                 background=self.background[act],
                                 foreground=self.foreground[act])
            self.choose_task.config(state="normal")
        else:
            self.on = True
            self.affiche()

    def ting(self):
        """ joue le son marquant le changement de période """
        if not CONFIG.getboolean("Pomodoro", "mute", fallback=False):
            Popen([CONFIG.get("Pomodoro", "player"),
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
                        self.activite.set(_("Work"))
                        self.tps = [CONFIG.getint("Pomodoro", "work_time"), 0]
                    act = self.activite.get()
                    self.style.configure('timer.pomodoro.TLabel',
                                         background=self.background[act],
                                         foreground=self.foreground[act])
            elif self.tps[1] == -1:
                self.tps[0] -= 1
                self.tps[1] = 59
            self.temps.configure(text="{0:02}:{1:02}".format(*self.tps))
            self.after(1000, self.affiche)
