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


Notification class and script
"""

from tkinter import Tk
from tkinter.ttk import Label, Button, Style
from subprocess import Popen
import sys
from constants import CONFIG, ICON_NOTIF, active_color


class Notification(Tk):
    def __init__(self, text=''):
        Tk.__init__(self)
        self.overrideredirect(True)
        self.withdraw()
        self.columnconfigure(0, weight=1)
        self.attributes('-type', 'notification')
        self.attributes('-alpha', 0.75)

        self.style = Style(self)
        self.style.theme_use('clam')
        self.bg = [CONFIG.get('Reminders', 'window_bg'),
                   CONFIG.get('Reminders', 'window_bg_alternate')]
        self.fg = [CONFIG.get('Reminders', 'window_fg'),
                   CONFIG.get('Reminders', 'window_fg_alternate')]
        self.active_bg = [active_color(*self.winfo_rgb(bg)) for bg in self.bg]
        self.active_bg2 = [active_color(*self.winfo_rgb(bg)) for bg in self.active_bg]
        self.style.configure('notif.TLabel', background=self.bg[0],
                             foreground=self.fg[0])
        self.style.configure('notif.TButton', background=self.active_bg[0],
                             relief='flat', foreground=self.fg[0])
        self.configure(bg=self.bg[0])
        self.style.map('notif.TButton', background=[('active', self.active_bg2[0])])
        Label(self, text=text, style='notif.TLabel').grid(row=0, column=0, padx=10, pady=10)
        Button(self, text='Ok', command=self.quit,
               style='notif.TButton').grid(row=1, column=0, padx=10, pady=(0, 10))
        self.blink_alternate = False
        self.deiconify()
        self.update_idletasks()
        self.geometry('%ix%i+0+0' % (self.winfo_screenwidth(), self.winfo_height()))
        self.alarm_id = ''
        self.alarm_process = None
        self.blink_id = ''
        self.timeout_id = ''
        if CONFIG.getboolean('Reminders', 'blink'):
            self.blink_id = self.after(500, self.blink)
        if not CONFIG.getboolean("Reminders", "mute", fallback=False):
            self.alarm()
        timeout = CONFIG.getint('Reminders', 'timeout') * 60 * 1000
        if timeout > 0:
            self.timeout_id = self.after(timeout, self.quit)

    def alarm(self):
        self.alarm_process = Popen([CONFIG.get("General", "soundplayer"),
                                    CONFIG.get("Reminders", "alarm")])
        self.alarm_id = self.after(500, self.repeat_alarm)

    def repeat_alarm(self):
        if self.alarm_process.poll() is None:
            self.alarm_id = self.after(500, self.repeat_alarm)
        else:  # ringing is finished
            self.alarm()

    def quit(self):
        try:
            self.after_cancel(self.alarm_id)
        except ValueError:
            pass
        try:
            self.after_cancel(self.blink_id)
        except ValueError:
            pass
        try:
            self.after_cancel(self.timeout_id)
        except ValueError:
            pass
        if self.alarm_process is not None:
            self.alarm_process.terminate()
        self.destroy()

    def blink(self):
        self.blink_alternate = not self.blink_alternate
        self.configure(bg=self.bg[self.blink_alternate])
        self.style.configure('notif.TLabel', background=self.bg[self.blink_alternate],
                             foreground=self.fg[self.blink_alternate])
        self.style.configure('notif.TButton', background=self.active_bg[self.blink_alternate],
                             relief='flat', foreground=self.fg[self.blink_alternate])
        self.blink_id = self.after(500, self.blink)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        text = sys.argv[1]
        if CONFIG.getboolean('Reminders', 'notification', fallback=True):
            try:
                Popen(["notify-send", "-i", ICON_NOTIF, "Scheduler", text])
            except Exception:
                pass  # notifications not supported
        if CONFIG.getboolean('Reminders', 'window', fallback=True):
            n = Notification(text)
            n.mainloop()
    else:
        n = Notification('test')
        n.mainloop()
