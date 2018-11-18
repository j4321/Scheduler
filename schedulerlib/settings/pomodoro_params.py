#! /usr/bin/python3
# -*-coding:Utf-8 -*

"""
WorkHourGlass - Enhance your efficiency by timing your work and breaks
Copyright 2015-2017 Juliette Monsel <j_4321@protonmail.com>

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

Settings GUI
"""

import os
from tkinter import BooleanVar, Canvas
from tkinter.ttk import Notebook, Style, Label, Separator, Frame, Entry, \
    Button, Checkbutton
from tkinter.messagebox import showerror
from schedulerlib.constants import COLOR, valide_entree_nb, CONFIG, askcolor, askopenfilename
from schedulerlib.ttkwidgets import AutoScrollbar
from PIL.ImageTk import PhotoImage
from .color import ColorFrame
from .opacity import OpacityFrame
from .font import FontFrame


class PomodoroParams(Frame):

    def __init__(self, parent, **options):
        """ créer le Toplevel permettant de modifier les paramètres """
        Frame.__init__(self, parent, **options)

        self.onglets = Notebook(self)
        self.onglets.pack(fill='both', expand=True)
        self.im_color = PhotoImage(master=self, file=COLOR)

        self.okfct = self.register(valide_entree_nb)

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
                             validatecommand=(self.okfct, '%d', '%S'),
                             validate='key')
        self.travail.insert(0, CONFIG.get("Pomodoro", "work_time"))
        self.travail.grid(row=0, column=1, padx=(0, 10))
        Label(self.time_frame, text=_("Break")).grid(row=0, column=2, padx=4)
        self.pause = Entry(self.time_frame, width=4, justify='center',
                           validatecommand=(self.okfct, '%d', '%S'),
                           validate='key')
        self.pause.insert(0, CONFIG.get("Pomodoro", "break_time"))
        self.pause.grid(row=0, column=3, padx=(0, 10))
        Label(self.time_frame, text=_("Rest")).grid(row=0, column=4, padx=4)
        self.rest = Entry(self.time_frame, width=4, justify='center',
                          validatecommand=(self.okfct, '%d', '%S'),
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

        # --- Son
        self.son = Frame(self.onglets, padding=10)
        self.son.columnconfigure(1, weight=1)
        self.onglets.add(self.son, text=_("Sound"))

        Label(self.son, text=_("Sound"),
              style='title.TLabel').grid(row=0, pady=4, padx=(2, 10), sticky="w")
        self.mute = BooleanVar(self, CONFIG.getboolean("Pomodoro", "mute"))

        b_son = Checkbutton(self.son, variable=self.mute, style='Mute')
        b_son.grid(row=0, column=1, sticky="w", pady=4, padx=10)
        self.son_frame = Frame(self.son)
        self.son_frame.grid(row=1, sticky="ew", columnspan=2)
        self.bip = Entry(self.son_frame)
        self.bip.insert(0, CONFIG.get("Pomodoro", "beep"))
        self.bip.pack(side="left", fill="both", expand=True)
        Button(self.son_frame, text="...", width=2, padding=0,
               command=self.choix_son).pack(side="right", padx=(2, 4))

        Separator(self.son, orient='horizontal').grid(row=2, columnspan=2,
                                                      sticky="ew", pady=10)
        son_frame2 = Frame(self.son)
        son_frame2.grid(row=3, sticky="ew", columnspan=2)
        Label(son_frame2, text=_("Audio player"),
              style='title.TLabel').pack(side="left", padx=(2, 10))
        self.player = Entry(son_frame2, justify='center')
        self.player.insert(0, CONFIG.get("Pomodoro", "player"))
        self.player.pack(side="right", fill="both", expand=True, padx=4)

        # --- Couleurs
        self.couleurs = Frame(self.onglets, padding=10)
        self.couleurs.columnconfigure(2, weight=1)
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
        self.bg.grid(row=0, column=1, sticky='e')
        self.fg.grid(row=1, column=1, sticky='e')
        Separator(self.couleurs, orient='horizontal').grid(row=2, sticky="ew",
                                                           pady=10, columnspan=3)
        Label(self.couleurs, text=_("Work"),
              style='title.TLabel').grid(row=3, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.work_bg.grid(row=3, column=1, sticky='e')
        self.work_fg.grid(row=4, column=1, sticky='e')
        Separator(self.couleurs, orient='horizontal').grid(row=5, sticky="ew",
                                                           pady=10, columnspan=3)
        Label(self.couleurs, text=_("Break"),
              style='title.TLabel').grid(row=6, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.break_bg.grid(row=6, column=1, sticky='e')
        self.break_fg.grid(row=7, column=1, sticky='e')
        Separator(self.couleurs, orient='horizontal').grid(row=8, sticky="ew",
                                                           pady=10, columnspan=3)
        Label(self.couleurs, text=_("Rest"),
              style='title.TLabel').grid(row=9, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        self.rest_bg.grid(row=9, column=1, sticky='e')
        self.rest_fg.grid(row=10, column=1, sticky='e')

        # --- Stats
        self.stats = Frame(self.onglets, padding=10)
        self.stats.columnconfigure(0, weight=1)
        self.stats.rowconfigure(0, weight=1)
        self.onglets.add(self.stats, text=_("Statistics"))
        can = Canvas(self.stats, bg=self.style.lookup('TFrame', 'background'),
                     highlightthickness=0, width=1,
                     relief='flat')
        scroll = AutoScrollbar(self.stats, orient='vertical', command=can.yview)
        can.configure(yscrollcommand=scroll.set)
        can.grid(row=0, column=0, sticky='ewns')
        scroll.grid(row=0, column=1, sticky='ns')
        task_frame = Frame(can)
        can.create_window(0, 0, anchor='nw', window=task_frame)

        tasks = [t.capitalize() for t in CONFIG.options("PomodoroTasks")]
        cmap = [CONFIG.get("PomodoroTasks", task) for task in tasks]
        self.tasks = {}
        for coul, task in zip(cmap, tasks):
            self.tasks[task] = ColorFrame(task_frame, coul, task)
            self.tasks[task].grid(sticky='e')
        self.update_idletasks()
        can.configure(width=task_frame.winfo_reqwidth())
        can.configure(scrollregion=can.bbox('all'))
        can.bind('<4>', lambda e: self._scroll(e, -1))
        can.bind('<5>', lambda e: self._scroll(e, 1))

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
        tpsw = int(self.travail.get())
        tpsp = int(self.pause.get())
        tpsr = int(self.rest.get())
        son = self.bip.get()
        player = CONFIG.get("Pomodoro", "player")
        mute = self.mute.get()
        font_prop = self.font.get_font()
        font = "{} {}".format(font_prop['family'].replace(' ', '\ '),
                              font_prop['size'])
        filetypes = ["ogg", "wav", "mp3"]

        if (tpsw > 0 and tpsp > 0 and tpsr > 0 and
           os.path.exists(son) and (son.split('.')[-1] in filetypes)):
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
            CONFIG.set("Pomodoro", "beep", son)
            CONFIG.set("Pomodoro", "player", player)
            CONFIG.set("Pomodoro", "mute", str(mute))
            for task, widget in self.tasks.items():
                CONFIG.set("PomodoroTasks", task, widget.get_color())

            return old_tpsw != tpsw or old_tpsp != tpsp or old_tpsr != old_tpsr
        else:
            showerror(_("Error"), _("There is at least one invalid setting!"))
            return False

    def choix_son(self):
        filetypes = [(_("sound file"), '*.mp3|*.ogg|*.wav'),
                     ('OGG', '*.ogg'),
                     ('MP3', '*.mp3'),
                     ('WAV', '*.wav')]
        init = self.bip.get()
        if not os.path.exists(init):
            init = CONFIG.get("Pomodoro", "beep")
        fich = askopenfilename(filetypes=filetypes, initialfile=os.path.split(init)[1],
                               initialdir=os.path.dirname(init), parent=self)
        if fich:
            self.bip.delete(0, "end")
            self.bip.insert(0, fich)
