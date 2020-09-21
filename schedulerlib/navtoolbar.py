#! /usr/bin/python3
# -*- coding: utf-8 -*-
# PEP8: ignore = E402,E501
"""
Scheduler - Task scheduling and calendar
Copyright 2003-2018 Matplotlib Development Team
Copyright 2018-2019 Juliette Monsel <j_4321@protonmail.com>

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


Adaptation of matplotlib.backends.backend_tkagg.NavigationToolbar2Tk to use
ttk.Button, translatable tooltips and tkfilebrowser.saveasfilename dialog.
"""
import tkinter as tk
from tkinter import ttk
import os.path

from PIL.ImageTk import PhotoImage
try:
    from tkfilebrowser import asksaveasfilename
except ImportError:
    from tkinter.filedialog import asksaveasfilename
try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
except ImportError:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar2Tk
from matplotlib.backends._backend_tk import ToolTip
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib import rcParams

from .messagebox import showerror
from .constants import IMAGES


class NavigationToolbar(NavigationToolbar2Tk):
    toolitems = (
        ('Home', _('Reset original view'), os.path.join(rcParams['datapath'], 'images', 'home.gif'), 'home'),
        ('Back', _('Back to previous view'), os.path.join(rcParams['datapath'], 'images', 'back.gif'), 'back'),
        ('Forward', _('Forward to next view'), os.path.join(rcParams['datapath'], 'images', 'forward.gif'), 'forward'),
        (None, None, None, None),
        ('Week', _('View last 7 days'), IMAGES['week'], 'view_week'),
        ('Month', _('View last 30 days'), IMAGES['month'], 'view_month'),
        (None, None, None, None),
        ('Pan', _('Pan axes with left mouse, zoom with right'), os.path.join(rcParams['datapath'], 'images', 'move.gif'), 'pan'),
        ('Zoom', _('Zoom to rectangle'), os.path.join(rcParams['datapath'], 'images', 'zoom_to_rect.gif'), 'zoom'),
        ('Subplots', _('Configure subplots'), os.path.join(rcParams['datapath'], 'images', 'subplots.gif'), 'configure_subplots'),
        ('Layout', _('Tight layout'), IMAGES['layout'], 'tight_layout'),
        ('Grid', _('Toggle grid'), IMAGES['grid'], 'toggle_grid'),
        (None, None, None, None),
        ('Save', _('Save the figure'), os.path.join(rcParams['datapath'], 'images', 'filesave.gif'), 'save_figure'),
    )

    def __init__(self, canvas, window, tight_layout_cmd, toggle_grid_cmd,
                 view_week_cmd, view_month_cmd, pack_toolbar=True):
        self.tight_layout = tight_layout_cmd
        self.toggle_grid = toggle_grid_cmd
        self.view_week = view_week_cmd
        self.view_month = view_month_cmd

        # Avoid using self.window (prefer self.canvas.get_tk_widget().master),
        # so that Tool implementations can reuse the methods.
        self.window = window

        tk.Frame.__init__(self, master=window, borderwidth=2,
                          width=int(canvas.figure.bbox.width), height=50)

        self._buttons = {}
        for text, tooltip_text, image_file, callback in self.toolitems:
            if text is None:
                # Add a spacer; return value is unused.
                self._Spacer()
            else:
                self._buttons[text] = button = self._Button(
                    text,
                    image_file,
                    toggle=callback in ["zoom", "pan"],
                    command=getattr(self, callback),
                )
                if tooltip_text is not None:
                    ToolTip.createToolTip(button, tooltip_text)

        self.message = tk.StringVar(master=self)
        self._message_label = tk.Label(master=self, textvariable=self.message)
        self._message_label.pack(side=tk.RIGHT)

        NavigationToolbar2.__init__(self, canvas)
        if pack_toolbar:
            self.pack(side=tk.BOTTOM, fill=tk.X)


    def save_figure(self, *args):
        filetypes = self.canvas.get_supported_filetypes().copy()
        default_filetype = self.canvas.get_default_filetype()

        # Tk doesn't provide a way to choose a default filetype,
        # so we just have to put it first
        default_filetype_name = filetypes.pop(default_filetype)
        sorted_filetypes = ([(default_filetype, default_filetype_name)]
                            + sorted(filetypes.items()))
        tk_filetypes = [(name, '*.%s' % ext) for ext, name in sorted_filetypes]

        # adding a default extension seems to break the
        # asksaveasfilename dialog when you choose various save types
        # from the dropdown.  Passing in the empty string seems to
        # work - JDH!
        # defaultextension = self.canvas.get_default_filetype()
        defaultextension = ''
        initialdir = os.path.expanduser(rcParams['savefig.directory'])
        initialfile = self.canvas.get_default_filename()
        fname = asksaveasfilename(
            master=self.window,
            title='Save the figure',
            filetypes=tk_filetypes,
            defaultextension=defaultextension,
            initialdir=initialdir,
            initialfile=initialfile,
        )

        if fname in ["", ()]:
            return
        # Save dir for next time, unless empty str (i.e., use cwd).
        if initialdir != "":
            rcParams['savefig.directory'] = (
                os.path.dirname(str(fname)))
        try:
            # This method will handle the delegation to the correct type
            self.canvas.figure.savefig(fname)
        except Exception as e:
            showerror(_("Error"), str(e))

    def _Button(self, text, image_file, toggle, command):
        im = PhotoImage(master=self, file=image_file)
        b = ttk.Button(master=self, text=text, padding=1, image=im, command=command,
                       style='nav.TButton')
        b._ntimage = im
        b.pack(side=tk.LEFT)
        return b

