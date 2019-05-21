#! /usr/bin/python3
# -*-coding:Utf-8 -*

"""
Scheduler - Task scheduling and calendar
Copyright 2015-2019 Juliette Monsel <j_4321@protonmail.com>

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

Settings GUI
"""
import os
import sqlite3
from tkinter import Canvas, Toplevel
from tkinter.ttk import Notebook, Style, Label, Separator, Frame, Entry, Button
from tkinter.messagebox import showerror, askyesno

from PIL.ImageTk import PhotoImage

from schedulerlib.constants import IM_COLOR, only_nb, CONFIG, askcolor, \
    CMAP, IM_ADD, IM_DEL, PATH_STATS, save_config, scrub
from schedulerlib.ttkwidgets import AutoScrollbar
from .color import ColorFrame
from .opacity import OpacityFrame
from .font import FontFrame
from .sound import SoundFrame


class PomodoroParams(Frame):

    def __init__(self, parent, **options):
        """ créer le Toplevel permettant de modifier les paramètres """
        Frame.__init__(self, parent, **options)

        self.onglets = Notebook(self)
        self.onglets.pack(fill='both', expand=True)
        self.im_color = PhotoImage(master=self, file=IM_COLOR)
        self.im_plus = PhotoImage(master=self, file=IM_ADD)
        self.im_moins = PhotoImage(master=self, file=IM_DEL)

        self.okfct = self.register(only_nb)

        self.style = Style(self)

        self.nb_task = len(CONFIG.options("PomodoroTasks"))

        # --- Général (temps, police et langue)
        self.general = Frame(self.onglets, padding=10)
        self.general.columnconfigure(1, weight=1)
        self.onglets.add(self.general, text=_("General"))

        # --- --- Temps
        Label(self.general, text=_("Times (min)"),
              style='title.TLabel').grid(row=0, pady=4, padx=(2, 10), sticky="w")
        self.time_frame = Frame(self.general)
        self.time_frame.grid(row=0, column=1, sticky="w", padx=4)
        Label(self.time_frame, text=_("Work")).grid(row=0, padx=4, column=0)
        self.travail = Entry(self.time_frame, width=4, justify='center',
                             validatecommand=(self.okfct, '%P'),
                             validate='key')
        self.travail.insert(0, CONFIG.get("Pomodoro", "work_time"))
        self.travail.grid(row=0, column=1, padx=(0, 10))
        Label(self.time_frame, text=_("Break")).grid(row=0, column=2, padx=4)
        self.pause = Entry(self.time_frame, width=4, justify='center',
                           validatecommand=(self.okfct, '%P'),
                           validate='key')
        self.pause.insert(0, CONFIG.get("Pomodoro", "break_time"))
        self.pause.grid(row=0, column=3, padx=(0, 10))
        Label(self.time_frame, text=_("Rest")).grid(row=0, column=4, padx=4)
        self.rest = Entry(self.time_frame, width=4, justify='center',
                          validatecommand=(self.okfct, '%P'),
                          validate='key')
        self.rest.insert(0, CONFIG.get("Pomodoro", "rest_time"))
        self.rest.grid(row=0, column=5)

        Separator(self.general,
                  orient='horizontal').grid(row=1, columnspan=2,
                                            sticky="ew", pady=10)

        # --- --- Police
        Label(self.general, text=_("Font"),
              style='title.TLabel').grid(row=2, sticky='nw', padx=(2, 10))
        self.font = FontFrame(self.general, font=CONFIG.get('Pomodoro', 'font'),
                              sample_text="02:17")
        self.font.grid(row=2, column=1, padx=4, sticky='w')

        Separator(self.general,
                  orient='horizontal').grid(row=3, columnspan=2,
                                            sticky="ew", pady=10)

        # --- --- Opacity
        self.opacity = OpacityFrame(self.general)
        self.opacity.grid(row=5, columnspan=2, sticky='w', padx=(2, 4), pady=4)

        Separator(self.general,
                  orient='horizontal').grid(row=6, columnspan=2,
                                            sticky="ew", pady=10)

        # --- --- Son
        self.sound = SoundFrame(self.general, CONFIG.get("Pomodoro", "beep"),
                                mute=CONFIG.getboolean("Pomodoro", "mute"),
                                label=_("Sound"), style='title.TLabel')
        self.sound.grid(row=7, columnspan=2, sticky='ew', pady=4)

        # --- Couleurs
        self.couleurs = Frame(self.onglets, padding=10)
        self.couleurs.columnconfigure(3, weight=1)
        self.onglets.add(self.couleurs, text=_("Colors"))

        self.bg = ColorFrame(self.couleurs,
                             CONFIG.get("Pomodoro", "background"),
                             _("Background"))
        self.work_bg = ColorFrame(self.couleurs,
                                  CONFIG.get("Pomodoro", "work_bg"),
                                  _("Background"))
        self.break_bg = ColorFrame(self.couleurs,
                                   CONFIG.get("Pomodoro", "break_bg"),
                                   _("Background"))
        self.rest_bg = ColorFrame(self.couleurs,
                                  CONFIG.get("Pomodoro", "rest_bg"),
                                  _("Background"))
        self.fg = ColorFrame(self.couleurs,
                             CONFIG.get("Pomodoro", "foreground"),
                             _("Foreground"))
        self.work_fg = ColorFrame(self.couleurs,
                                  CONFIG.get("Pomodoro", "work_fg"),
                                  _("Foreground"))
        self.break_fg = ColorFrame(self.couleurs,
                                   CONFIG.get("Pomodoro", "break_fg"),
                                   _("Foreground"))
        self.rest_fg = ColorFrame(self.couleurs,
                                  CONFIG.get("Pomodoro", "rest_fg"),
                                  _("Foreground"))

        Label(self.couleurs, text=_("General"),
              style='title.TLabel').grid(row=0, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.bg.grid(row=0, column=1, sticky='e', padx=8, pady=4)
        self.fg.grid(row=0, column=2, sticky='e', padx=8, pady=4)
        Separator(self.couleurs, orient='horizontal').grid(row=1, sticky="ew",
                                                           pady=10, columnspan=4)
        Label(self.couleurs, text=_("Work"),
              style='title.TLabel').grid(row=2, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.work_bg.grid(row=2, column=1, sticky='e', padx=8, pady=4)
        self.work_fg.grid(row=2, column=2, sticky='e', padx=8, pady=4)
        Separator(self.couleurs, orient='horizontal').grid(row=3, sticky="ew",
                                                           pady=10, columnspan=4)
        Label(self.couleurs, text=_("Break"),
              style='title.TLabel').grid(row=4, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.break_bg.grid(row=4, column=1, sticky='e', padx=8, pady=4)
        self.break_fg.grid(row=4, column=2, sticky='e', padx=8, pady=4)
        Separator(self.couleurs, orient='horizontal').grid(row=5, sticky="ew",
                                                           pady=10, columnspan=4)
        Label(self.couleurs, text=_("Rest"),
              style='title.TLabel').grid(row=6, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.rest_bg.grid(row=6, column=1, sticky='e', padx=8, pady=4)
        self.rest_fg.grid(row=6, column=2, sticky='e', padx=8, pady=4)

        # --- Tasks
        self.stats = Frame(self.onglets, padding=10)
        self.stats.columnconfigure(0, weight=1)
        self.stats.rowconfigure(2, weight=1)
        self.onglets.add(self.stats, text=_("Tasks"))
        # graph legend
        legend_frame = Frame(self.stats)
        Label(legend_frame, style='title.TLabel',
              text=_('Maximum number of rows in the legend')).pack(side='left')
        self.legend_row_nb = Entry(legend_frame, width=4, justify='center',
                                   validatecommand=(self.okfct, '%P'),
                                   validate='key')
        self.legend_row_nb.insert(0, CONFIG.get('Pomodoro', 'legend_max_height', fallback='6'))
        self.legend_row_nb.pack(side='left', padx=4)

        # task colors
        can = Canvas(self.stats, bg=self.style.lookup('TFrame', 'background'),
                     highlightthickness=0, width=1,
                     relief='flat')
        scroll = AutoScrollbar(self.stats, orient='vertical', command=can.yview)
        can.configure(yscrollcommand=scroll.set)
        self.task_frame = Frame(can)
        can.create_window(0, 0, anchor='nw', window=self.task_frame)

        tasks = CONFIG.options("PomodoroTasks")
        tasks.sort()
        cmap = [CONFIG.get("PomodoroTasks", task) for task in tasks]
        self.tasks = {}
        self._tasks_btns = {}
        for i, (coul, task) in enumerate(zip(cmap, tasks)):
            self.tasks[task] = ColorFrame(self.task_frame, coul, task.capitalize())
            self.tasks[task].grid(row=i, column=0, sticky='e', padx=4, pady=4)
            b = Button(self.task_frame, image=self.im_moins, padding=2,
                       command=lambda t=task: self.del_task(t))
            b.grid(row=i, column=1, sticky='w', padx=4, pady=4)
            self._tasks_btns[task] = b
        if len(tasks) == 1:
            self._tasks_btns[tasks[0]].state(['disabled'])

        legend_frame.grid(row=0, columnspan=2, sticky='w', pady=4)
        Label(self.stats, text=_('Colors in the statistic graph'),
              style='title.TLabel').grid(row=1, column=0, sticky='w', pady=4)
        can.grid(row=2, column=0, sticky='ewns')
        scroll.grid(row=2, column=1, sticky='ns')
        Button(self.stats, image=self.im_plus, command=self.add_task).grid(row=3, column=0, sticky='w')

        self.update_idletasks()
        can.configure(width=self.task_frame.winfo_reqwidth())
        can.configure(scrollregion=can.bbox('all'))
        can.bind('<4>', lambda e: self._scroll(e, -1))
        can.bind('<5>', lambda e: self._scroll(e, 1))
        self.task_frame.bind('<Configure>', lambda e: can.configure(scrollregion=can.bbox('all')))

    def _scroll(self, event, delta):
        if event.widget.yview() != (0, 1):
            event.widget.yview_scroll(delta, 'units')

    def choix_couleur(self, type_mode):
        """ sélection de la couleur du fond/texte pour chaque mode (travail/pause/repos) """
        coul = askcolor(self.style.lookup(type_mode + ".TButton", 'background'), parent=self)
        if coul:
            self.style.configure(type_mode + ".TButton", background=coul)

    def coul_stat(self, i):
        """ choix des couleurs pour l'affichage des stats """
        coul = askcolor(self.style.lookup("t%i.TButton" % i, "background"), parent=self)
        if coul:
            self.style.configure("t%i.TButton" % i, background=coul)

    def valide(self):
        """Update config and return whether the pomodor timer should be stopped."""
        old_tpsw = CONFIG.getint("Pomodoro", "work_time")
        old_tpsp = CONFIG.getint("Pomodoro", "break_time")
        old_tpsr = CONFIG.getint("Pomodoro", "rest_time")
        try:
            tpsw = int(self.travail.get())
        except ValueError:  # empty entry
            tpsw = 0
        if tpsw == 0:
            tpsw = old_tpsw
        try:
            tpsp = int(self.pause.get())
        except ValueError:
            tpsp = 0
        if tpsp == 0:
            tpsp = old_tpsp
        try:
            tpsr = int(self.rest.get())
        except ValueError:
            tpsr = 0
        if tpsr == 0:
            tpsr = old_tpsr

        sound, mute = self.sound.get()
        font_prop = self.font.get_font()
        font = "{} {}".format(font_prop['family'].replace(' ', '\ '),
                              font_prop['size'])
        try:
            legend_rows = int(self.legend_row_nb.get())
        except ValueError:
            legend_rows = 0
        if legend_rows == 0:
            legend_rows = CONFIG.getint("Pomodoro", "legend_max_height")

        if not os.path.exists(sound):
            showerror(_("Error"), _("The file {filepath} does not exists, the old file will be used.").format(filepath=sound))
            sound = CONFIG.get("Pomodoro", "beep")

        CONFIG.set("Pomodoro", "alpha", str(self.opacity.get_opacity()))
        CONFIG.set("Pomodoro", "font", font)
        CONFIG.set("Pomodoro", "background", self.bg.get_color())
        CONFIG.set("Pomodoro", "foreground", self.fg.get_color())
        CONFIG.set("Pomodoro", "work_time", str(tpsw))
        CONFIG.set("Pomodoro", "work_bg", self.work_bg.get_color())
        CONFIG.set("Pomodoro", "work_fg", self.work_fg.get_color())
        CONFIG.set("Pomodoro", "break_time", str(tpsp))
        CONFIG.set("Pomodoro", "break_bg", self.break_bg.get_color())
        CONFIG.set("Pomodoro", "break_fg", self.break_fg.get_color())
        CONFIG.set("Pomodoro", "rest_time", str(tpsr))
        CONFIG.set("Pomodoro", "rest_bg", self.rest_bg.get_color())
        CONFIG.set("Pomodoro", "rest_fg", self.rest_fg.get_color())
        CONFIG.set("Pomodoro", "beep", sound)
        CONFIG.set("Pomodoro", "mute", str(mute))
        CONFIG.set("Pomodoro", "legend_max_height", str(legend_rows))
        for task, widget in self.tasks.items():
            CONFIG.set("PomodoroTasks", task, widget.get_color())

        return old_tpsw != tpsw or old_tpsp != tpsp or old_tpsr != old_tpsr

    def del_task(self, task):
        """ Suppression de tâches """
        rep = askyesno(_("Confirmation"),
                       _("Are you sure you want to delete the task {task}? This action cannot be undone.").format(task=task.capitalize()))
        if rep:
            CONFIG.remove_option("PomodoroTasks", task)
            # remove stats
            db = sqlite3.connect(PATH_STATS)
            cursor = db.cursor()
            try:
                cursor.execute('DROP TABLE {}'.format(scrub(task.lower().replace(' ', '_'))))
                db.commit()
            except sqlite3.OperationalError:
                pass   # no stats yet
            db.close()
            self.tasks[task].destroy()
            self._tasks_btns[task].destroy()
            del self.tasks[task]
            del self._tasks_btns[task]

            if len(CONFIG.options("PomodoroTasks")) == 1:
                CONFIG.set("PomodoroTasks", _("Work"), CMAP[0])
                self._tasks_btns[CONFIG.options("PomodoroTasks")[0]].state(['disabled'])
            save_config()

    def add_task(self):

        def ajoute(event=None):
            task = nom.get().lower().strip()
            if task in self.tasks:
                showerror(_("Error"),
                          _("The task {task} already exists.").format(task=task),
                          parent=self)

            elif task:
                coul = CMAP[(len(self.tasks) + 1) % len(CMAP)]
                i = self.task_frame.grid_size()[1] + 1
                self.tasks[task] = ColorFrame(self.task_frame, coul, task.capitalize())
                self.tasks[task].grid(row=i, column=0, sticky='e', padx=4, pady=4)
                b = Button(self.task_frame, image=self.im_moins, padding=2,
                           command=lambda t=task: self.del_task(t))
                b.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                self._tasks_btns[task] = b
                self._tasks_btns[CONFIG.options("PomodoroTasks")[0]].state(['!disabled'])
            top.destroy()

        top = Toplevel(self)
        top.title(_("New task"))
        top.transient(self)
        top.grab_set()
        nom = Entry(top, width=20, justify='center')
        nom.grid(row=0, columnspan=2, sticky="ew")
        nom.focus_set()
        nom.bind('<Key-Return>', ajoute)
        Button(top, text=_("Cancel"), command=top.destroy).grid(row=1, column=0)
        Button(top, text=_("Ok"), command=ajoute).grid(row=1, column=1)
        top.wait_window(top)
