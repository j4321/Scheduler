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
from tkinter import Toplevel, PhotoImage, StringVar, Menu, BooleanVar
from tkinter.ttk import Notebook, Style, Label, Separator, Frame, Entry, \
    Menubutton, Button, Checkbutton
from tkinter.messagebox import showerror, showinfo
from .constants import COLOR, valide_entree_nb, CONFIG, LANGUES, save_config, askcolor, askopenfilename


class Params(Toplevel):

    def __init__(self, parent, **options):
        """ créer le Toplevel permettant de modifier les paramètres """
        Toplevel.__init__(self, parent, **options)
        self.grab_set()
        self.transient(parent)
        self.title(_("Pomodoro Settings"))
        self.resizable(0, 0)

        self.onglets = Notebook(self)
        self.onglets.grid(row=0, column=0, columnspan=2)
        self.im_color = PhotoImage(master=self, file=COLOR)

        self.okfct = self.register(valide_entree_nb)

        self.style = Style(self)

        self.nb_task = len(CONFIG.options("PomodoroTasks"))

        # --- Général (temps, police et langue)
        self.general = Frame(self.onglets, padding=10)
        self.general.pack(fill="both", expand=True, padx=10, pady=10)
        self.onglets.add(self.general, text=_("General"))

        # --- --- Temps
        Label(self.general, text=_("Times:"),
              style='title.TLabel').grid(row=0, pady=4, sticky="w")
        self.time_frame = Frame(self.general)
        self.time_frame.grid(row=1, sticky="ew")
        Label(self.time_frame, text=_("Work: ")).grid(row=0, column=0)
        self.travail = Entry(self.time_frame, width=4, justify='center',
                             validatecommand=(self.okfct, '%d', '%S'),
                             validate='key')
        self.travail.insert(0, CONFIG.get("Pomodoro", "work_time"))
        self.travail.grid(row=0, column=1, padx=(0, 10))
        Label(self.time_frame, text=_("Break: ")).grid(row=0, column=2)
        self.pause = Entry(self.time_frame, width=4, justify='center',
                           validatecommand=(self.okfct, '%d', '%S'),
                           validate='key')
        self.pause.insert(0, CONFIG.get("Pomodoro", "break_time"))
        self.pause.grid(row=0, column=3, padx=(0, 10))
        Label(self.time_frame, text=_("Rest: ")).grid(row=0, column=4)
        self.rest = Entry(self.time_frame, width=4, justify='center',
                          validatecommand=(self.okfct, '%d', '%S'),
                          validate='key')
        self.rest.insert(0, CONFIG.get("Pomodoro", "rest_time"))
        self.rest.grid(row=0, column=5)

        Separator(self.general,
                  orient='horizontal').grid(row=2, sticky="ew", pady=10)

        # --- --- Police
        self.font_frame = Frame(self.general)
        self.font_frame.grid(row=3, pady=4, sticky="ew")
        Label(self.font_frame, text=_("Font:"),
              style='title.TLabel').pack(anchor="n", side="left")
        self.exemple = Label(self.font_frame, text="02:17", anchor="center",
                             style='ex.TLabel', padding=2,
                             font="%s %i" % (CONFIG.get("Pomodoro", "font"), CONFIG.getint("Pomodoro", "fontsize")),
                             relief="groove")
        self.exemple.pack(side="right")
        self.font_frame2 = Frame(self.general)
        self.font_frame2.grid(row=4)
        Label(self.font_frame2, text=_("Family: ")).grid(row=0, column=0, sticky="e")
        self.font = Entry(self.font_frame2, justify='center')
        self.font.insert(0, CONFIG.get("Pomodoro", "font"))
        self.font.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        self.font.bind('<FocusOut>', self.actualise_police)
        self.font.bind('<Key-Return>', self.actualise_police, True)
        Label(self.font_frame2, text=_("Size: ")).grid(row=0, column=2, sticky="e")
        self.size = Entry(self.font_frame2, width=4, justify='center',
                          validatecommand=(self.okfct, '%d', '%S'),
                          validate='key')
        self.size.insert(0, CONFIG.getint("Pomodoro", "fontsize"))
        self.size.grid(row=0, column=3, pady=2, sticky="w")
        self.size.bind('<FocusOut>', self.actualise_police)
        self.size.bind('<Key-Return>', self.actualise_police, True)

        Separator(self.general,
                  orient='horizontal').grid(row=5, sticky="ew", pady=10)

        # --- --- Langues
        self.lang_frame = Frame(self.general)
        self.lang_frame.grid(row=6, pady=4, sticky="ew")
        Label(self.lang_frame, text=_("Language:"),
              style='title.TLabel').pack(side="left")
        self.lang = StringVar(self.lang_frame, LANGUES[CONFIG.get("General", "language")])
        b_lang = Menubutton(self.lang_frame, textvariable=self.lang)
        menu = Menu(b_lang, tearoff=False)
        menu.add_radiobutton(label="English", variable=self.lang,
                             value="English", command=self.change_langue)
        menu.add_radiobutton(label="Français", variable=self.lang,
                             value="Français", command=self.change_langue)
        b_lang.configure(menu=menu)
        b_lang.pack(side="right")

        # --- Son
        self.son = Frame(self.onglets, padding=10)
        self.son.pack(fill="both", expand=True, padx=10, pady=10)
        self.son.columnconfigure(1, weight=1)
        self.onglets.add(self.son, text=_("Sound"))

        Label(self.son, text=_("Sound:"),
              style='title.TLabel').grid(row=0, pady=4, sticky="w")
        self.mute = BooleanVar(self, CONFIG.getboolean("Pomodoro", "mute"))

        b_son = Checkbutton(self.son, variable=self.mute, style='Mute')
        b_son.grid(row=0, column=1, sticky="w", pady=4)
        self.son_frame = Frame(self.son)
        self.son_frame.grid(row=1, sticky="ew", columnspan=2)
        self.bip = Entry(self.son_frame, justify='center')
        self.bip.insert(0, CONFIG.get("Pomodoro", "beep"))
        self.bip.pack(side="left", fill="both", expand=True)
        Button(self.son_frame, text="...", width=2, padding=0,
               command=self.choix_son).pack(side="right", padx=(2, 0))

        Separator(self.son, orient='horizontal').grid(row=2, columnspan=2,
                                                      sticky="ew", pady=10)
        son_frame2 = Frame(self.son)
        son_frame2.grid(row=3, sticky="ew", columnspan=2)
        Label(son_frame2, text=_("Audio player: "),
              style='title.TLabel').pack(side="left")
        self.player = Entry(son_frame2, justify='center')
        self.player.insert(0, CONFIG.get("Pomodoro", "player"))
        self.player.pack(side="right", fill="both", expand=True)

        # --- Couleurs
        self.couleurs = Frame(self.onglets, padding=10)
        self.couleurs.pack(fill="both", expand=True, padx=10, pady=10)
        self.onglets.add(self.couleurs, text=_("Colors"))

        # --- ---  style des boutons de choix des couleurs
        self.style.configure("fond_w.TButton", background=CONFIG.get("Pomodoro", "work_bg"))
        self.style.configure("fond_p.TButton", background=CONFIG.get("Pomodoro", "break_bg"))
        self.style.configure("fond_r.TButton", background=CONFIG.get("Pomodoro", "rest_bg"))
        self.style.configure("texte_w.TButton", background=CONFIG.get("Pomodoro", "work_fg"))
        self.style.configure("texte_p.TButton", background=CONFIG.get("Pomodoro", "break_fg"))
        self.style.configure("texte_r.TButton", background=CONFIG.get("Pomodoro", "rest_fg"))
        self.couleurs.grid_columnconfigure(3, weight=3)
        self.couleurs.grid_rowconfigure(0, weight=1)
        Label(self.couleurs, text=_("Work: "),
              style='title.TLabel').grid(row=0, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        Label(self.couleurs, text=_("Background: ")).grid(row=0, column=1,
                                                          sticky="e", pady=(6, 4))
        Button(self.couleurs, width=2, command=lambda: self.choix_couleur("fond_w"),
               style='fond_w.TButton').grid(row=0, column=2, pady=4)
        Label(self.couleurs, text=_("Text: ")).grid(row=1, column=1, sticky="e")
        Button(self.couleurs, width=2, command=lambda: self.choix_couleur("texte_w"),
               style='texte_w.TButton').grid(row=1, column=2, pady=4)

        Separator(self.couleurs, orient='horizontal').grid(row=2, sticky="ew",
                                                           pady=10, columnspan=4)

        Label(self.couleurs, text=_("Break: "),
              style='title.TLabel').grid(row=3, column=0, pady=4,
                                         padx=(2, 10), sticky="w")
        Label(self.couleurs, text=_("Background: ")).grid(row=3, column=1,
                                                          sticky="e", pady=(6, 4))
        Button(self.couleurs, width=2, command=lambda: self.choix_couleur("fond_p"),
               style='fond_p.TButton').grid(row=3, column=2, pady=4)
        Label(self.couleurs, text=_("Text: ")).grid(row=4, column=1, sticky="e")
        Button(self.couleurs, width=2, command=lambda: self.choix_couleur("texte_p"),
               style='texte_p.TButton').grid(row=4, column=2, pady=4)

        Separator(self.couleurs, orient='horizontal').grid(row=5, sticky="ew",
                                                           pady=10, columnspan=4)

        Label(self.couleurs, text=_("Rest: "),
              style='title.TLabel').grid(row=6, column=0, pady=4,
                                         sticky="w", padx=(2, 10))
        Label(self.couleurs, text=_("Background: ")).grid(row=6, column=1,
                                                          sticky="e", pady=(6, 4))
        Button(self.couleurs, width=2, command=lambda: self.choix_couleur("fond_r"),
               style='fond_r.TButton').grid(row=6, column=2, pady=4)
        Label(self.couleurs, text=_("Text: ")).grid(row=7, column=1, sticky="e")
        Button(self.couleurs, width=2, command=lambda: self.choix_couleur("texte_r"),
               style='texte_r.TButton').grid(row=7, column=2, pady=4)

        # --- Stats
        self.stats = Frame(self.onglets, padding=10)
        self.stats.pack(fill="both", expand=True, padx=10, pady=10)
        self.stats.grid_columnconfigure(2, weight=1)
        self.onglets.add(self.stats, text=_("Statistics"))

        Label(self.stats, text=_("Statistics:"),
              style='title.TLabel').grid(row=0, column=0, pady=4, sticky="w")

        tasks = [t.capitalize() for t in CONFIG.options("PomodoroTasks")]
        cmap = [CONFIG.get("PomodoroTasks", task) for task in tasks]
        for i, coul, task in zip(range(self.nb_task), cmap, tasks):
            Label(self.stats, text=task).grid(row=i + 1, column=0, sticky="e",
                                              padx=4, pady=4)
            self.style.configure("t%i.TButton" % i, background=coul)
            Button(self.stats, style="t%i.TButton" % i, width=2,
                   command=lambda j=i: self.coul_stat(j)).grid(row=i + 1,
                                                               column=1, pady=4)

        # --- Validation
        Button(self, text="Ok", command=self.valide).grid(row=1, column=1, sticky="we")
        Button(self, text=_("Cancel"), command=self.destroy).grid(row=1, column=0, sticky="we")

    def actualise_police(self, event):
        """ actualise le texte d'exemple de la police choisie """
        family = self.font.get()
        family = "\ ".join(family.split(" "))
        self.exemple.configure(font="%s %s" % (family, self.size.get()))

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
        old_tpsw = CONFIG.getint("Pomodoro", "work_time")
        old_tpsp = CONFIG.getint("Pomodoro", "break_time")
        old_tpsr = CONFIG.getint("Pomodoro", "rest_time")
        tpsw = int(self.travail.get())
        tpsp = int(self.pause.get())
        tpsr = int(self.rest.get())
        pausefg = self.style.lookup("texte_p.TButton", "background")
        pausebg = self.style.lookup("fond_p.TButton", "background")
        workfg = self.style.lookup("texte_w.TButton", "background")
        workbg = self.style.lookup("fond_w.TButton", "background")
        restfg = self.style.lookup("texte_r.TButton", "background")
        restbg = self.style.lookup("fond_r.TButton", "background")
        son = self.bip.get()
        player = CONFIG.get("Pomodoro", "player")
        mute = self.mute.get()
        family = self.font.get()
        family = "\ ".join(family.split(" "))
        size = self.size.get()
        cmap = []
        for i in range(self.nb_task):
            cmap.append(self.style.lookup("t%i.TButton" % i, "background"))

        filetypes = ["ogg", "wav", "mp3"]
        if (tpsw > 0 and tpsp > 0 and tpsr > 0 and
           os.path.exists(son) and (son.split('.')[-1] in filetypes)):
            CONFIG.set("General", "language", self.lang.get()[:2].lower())
            CONFIG.set("Pomodoro", "font", family)
            CONFIG.set("Pomodoro", "fontsize", size)
            CONFIG.set("Pomodoro", "work_time", str(tpsw))
            CONFIG.set("Pomodoro", "work_bg", workbg)
            CONFIG.set("Pomodoro", "work_fg", workfg)
            CONFIG.set("Pomodoro", "break_time", str(tpsp))
            CONFIG.set("Pomodoro", "break_bg", pausebg)
            CONFIG.set("Pomodoro", "break_fg", pausefg)
            CONFIG.set("Pomodoro", "rest_time", str(tpsr))
            CONFIG.set("Pomodoro", "rest_bg", restbg)
            CONFIG.set("Pomodoro", "rest_fg", restfg)
            CONFIG.set("Pomodoro", "beep", son)
            CONFIG.set("Pomodoro", "player", player)
            CONFIG.set("Pomodoro", "mute", str(mute))
            for task, col in zip(CONFIG.options("PomodoroTasks"), cmap):
                CONFIG.set("PomodoroTasks", task, col)
            self.master.set_config()

            save_config()
            if (old_tpsw != CONFIG.getint("Pomodoro", "work_time") or
               old_tpsp != CONFIG.getint("Pomodoro", "break_time") or
               old_tpsr != CONFIG.getint("Pomodoro", "rest_time")):
                self.master.stop(False)

            self.destroy()
        else:
            showerror(_("Error"), _("There is at least one invalid setting!"))

    def change_langue(self):
        showinfo(_("Information"),
                 _("The language setting will take effect after restarting the application."),
                 parent=self)

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
