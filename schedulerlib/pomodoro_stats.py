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



Pomodoro stats viewer
"""
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from schedulerlib.constants import CONFIG, PATH_STATS, scrub
from schedulerlib.navtoolbar import NavigationToolbar
import datetime as dt
import numpy as np
import sqlite3


class Stats(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master, class_='Scheduler')
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
        db = sqlite3.connect(PATH_STATS)
        cursor = db.cursor()
        for i, task in enumerate(tasks):
            name = task.lower().replace(' ', '_')
            try:
                cursor.execute('SELECT date, work FROM {}'.format(scrub(name)))
                data = cursor.fetchall()
            except sqlite3.OperationalError:
                # task was never worked
                stats_x.append([demain - 1])
                stats_y.append(np.array([0]))
            else:
                no_data = False
                x = []
                y = []
                for date, work in data:
                    x.append(date)
                    y.append(work / 60)
                min_x = min(x[0], min_x)
                stats_x.append(x)
                stats_y.append(y)
        db.close()

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
            self.ax.xaxis.set_major_formatter(DateFormatter('%x'))
            self.ax.set_xlim(min_x - 0.5, demain - 0.5)
            self.ax.set_ylabel(_("time (h)"))
            self.ax.set_xlabel(_("date"))
            self.ax.xaxis_date()
            rows = CONFIG.getint("Pomodoro", "legend_max_height", fallback=6)
            ncol = int(np.ceil(len(tasks) / rows))

            lgd = self.ax.legend(fontsize=10, ncol=ncol, columnspacing=0.7, handlelength=0.9, handletextpad=0.5)
            try:
                lgd.set_draggable(True)
            except AttributeError:
                lgd.draggable(True)
            max_y = yy0.max()
            self.ax.set_ylim(0, max_y + 0.1 * max_y)
            self.ax.tick_params('x', rotation=70)
            self.update_idletasks()
            self.fig.tight_layout()
        self.figAgg.draw()
        self.toolbar.push_current()
        self.ax.set_xlim(max(demain - 30, min_x) - 0.5, demain - 0.5)
        self.toolbar.push_current()
        self.figAgg.draw()
