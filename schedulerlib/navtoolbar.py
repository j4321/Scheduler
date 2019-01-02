#! /usr/bin/python3
# -*- coding: utf-8 -*-
# PEP8: ignore = E402,E501
"""
Scheduler - Task scheduling and calendar
Copyright 2003-2018 Matplotlib Development Team
Copyright 2018 Juliette Monsel <j_4321@protonmail.com>

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
from .messagebox import showerror
from .constants import IM_LAYOUT, IM_GRID
try:
	from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
except ImportError:
	from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar2Tk
import os.path
from matplotlib import rcParams
try:
    from tkfilebrowser import asksaveasfilename
except ImportError:
    from tkinter.filedialog import asksaveasfilename
from PIL.ImageTk import PhotoImage


class NavigationToolbar(NavigationToolbar2Tk):
    toolitems = (
        ('Home', _('Reset original view'), os.path.join(rcParams['datapath'], 'images', 'home.gif'), 'home'),
        ('Back', _('Back to previous view'), os.path.join(rcParams['datapath'], 'images', 'back.gif'), 'back'),
        ('Forward', _('Forward to next view'), os.path.join(rcParams['datapath'], 'images', 'forward.gif'), 'forward'),
        (None, None, None, None),
        ('Pan', _('Pan axes with left mouse, zoom with right'), os.path.join(rcParams['datapath'], 'images', 'move.gif'), 'pan'),
        ('Zoom', _('Zoom to rectangle'), os.path.join(rcParams['datapath'], 'images', 'zoom_to_rect.gif'), 'zoom'),
        ('Subplots', _('Configure subplots'), os.path.join(rcParams['datapath'], 'images', 'subplots.gif'), 'configure_subplots'),
        ('Layout', _('Tight layout'), IM_LAYOUT, 'tight_layout'),
        ('Grid', _('Toggle grid'), IM_GRID, 'toggle_grid'),
        (None, None, None, None),
        ('Save', _('Save the figure'), os.path.join(rcParams['datapath'], 'images', 'filesave.gif'), 'save_figure'),
    )

    def __init__(self, canvas, window, tight_layout_cmd, toggle_grid_cmd):
        self.tight_layout = tight_layout_cmd
        self.toggle_grid = toggle_grid_cmd
        NavigationToolbar2Tk.__init__(self, canvas, window)

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

    def _Button(self, text, file, command, **kwargs):
        im = PhotoImage(master=self, file=file)
        b = ttk.Button(master=self, text=text, padding=1, image=im, command=command)
        b._ntimage = im
        b.pack(side=tk.LEFT)
        return b
