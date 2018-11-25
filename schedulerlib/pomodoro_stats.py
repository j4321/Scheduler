#! /usr/bin/python3
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



Pomodoro stats viewer
"""
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from schedulerlib.constants import CONFIG, PATH_STATS
from schedulerlib.navtoolbar import NavigationToolbar
import datetime as dt
import os
import numpy as np


class Stats(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title(_('Pomodoro - statistics'))

        bg = self.winfo_toplevel()['bg']
        self.fig = Figure(dpi=100, facecolor=bg)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.figAgg = FigureCanvasTkAgg(self.fig, self)
        self.figAgg.draw()
        self.figAgg.get_tk_widget().pack(fill='both', expand=True)
        self.figAgg.get_tk_widget().configure(bg=bg)
        self.toolbar = NavigationToolbar(self.figAgg, self, self.tight_layout, self.toggle_grid)

        self.plot_stats()

    def toggle_grid(self):
        self.ax.grid()
        self.figAgg.draw()

    def tight_layout(self):
        self.fig.tight_layout()
        self.figAgg.draw()

    def plot_stats(self):
        tasks = [t.capitalize() for t in CONFIG.options("PomodoroTasks")]
        tasks.sort()
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
                stat = np.loadtxt(chemin, dtype=int)
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
                stats_y.append(np.array([0]))

        # plots
        xx = np.arange(min_x, demain, dtype=float)
        yy0 = np.zeros_like(xx)  # pour empiler les stats
        if not no_data:
            for (i, task), x, y in zip(enumerate(tasks), stats_x, stats_y):
                yy = np.array([], dtype=int)
                # comble les trous par des 0
                # ainsi, les jours où une tâche n'a pas été travaillée correspondent
                # à des 0 sur le graph
                xxx = np.arange(min_x, x[0])
                yy = np.concatenate((yy, np.zeros_like(xxx, dtype=int)))
                for j in range(len(x) - 1):
                    xxx = np.arange(x[j], x[j + 1])
                    yy = np.concatenate((yy, [y[j]], np.zeros(len(xxx) - 1, dtype=int)))
                xxx = np.arange(x[-1], demain)
                yy = np.concatenate((yy, [y[-1]], np.zeros(len(xxx) - 1, dtype=int)))
                self.ax.bar(xx, yy, bottom=yy0, width=0.8, label=task, color=coul[i])
                yy0 += yy
            axx = np.array([int(xt) for xt in self.ax.get_xticks() if xt.is_integer()])
            self.ax.set_xticks(axx)
            self.ax.set_xticklabels([dt.date.fromordinal(i).strftime("%x") for i in axx])
            # plt.gcf().autofmt_xdate()
            self.ax.set_xlim(min_x - 0.5, demain - 0.5)
            self.ax.set_ylabel(_("time (h)"))
            self.ax.set_xlabel(_("date"))
            self.ax.xaxis_date()
            lgd = self.ax.legend(fontsize=10)
            lgd.set_draggable(True)
            max_y = yy0.max()
            self.ax.set_ylim(0, max_y + 0.1 * max_y)
            self.ax.tick_params('x', rotation=70)
            self.update_idletasks()
            self.fig.tight_layout()
        self.figAgg.draw()
