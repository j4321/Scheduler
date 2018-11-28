Scheduler - Alarms and reminders
================================
|Linux| |License|

System tray application for Linux to schedule events with possibity to set reminders. 
It also provides the following desktop widgets:

- a calendar to display and add events
- the list of the week's events
- a list of tasks
- a timer
- a pomodoro timer (https://en.wikipedia.org/wiki/Pomodoro_Technique) recording statistics

Prerequisites
-------------
Python 3 and the following librairies:

     - Tkinter (Python wrapper for Tk)
     - `ewmh <https://pypi.python.org/pypi/ewmh>`_
     - `Pillow <https://pypi.python.org/pypi/Pillow>`_
     - `APScheduler <https://pypi.python.org/pypi/apscheduler>`_
     - `matplotlib <https://matplotlib.org/>`_
     - `numpy <https://www.numpy.org/>`_
 
It is also necessary to have at least one of the following GUI toolkits for the system tray icon:
    
     - `Tktray <https://code.google.com/archive/p/tktray/downloads>`_
     - `PyGTK <http://www.pygtk.org/downloads.html>`_
     - PyQt5, PyQt4 or PySide
     
Optional dependencies:
    
    - libnotify and a notification server if your desktop environment does not provide one.
      (see https://wiki.archlinux.org/index.php/Desktop_notifications for more details): reminders as notifications
    - `tkcolorpicker <https://pypi.python.org/pypi/tkcolorpicker>`_ or zenity: nicer color chooser
    - any command line sound player (aplay, cvlc, ...): sounds for the reminders and the pomodoro timer

Install
------- 

::

    $ sudo python3 setup.py install

Scheduler can then be launched from *Menu > Utility > Scheduler* or directly from the command line with `scheduler`.


Troubleshooting
---------------

Several gui toolkits are available to display the system tray icon, so if the
icon does not behave properly, try to change toolkit, they are not all fully
compatible with every desktop environment.

If you encounter bugs or if you have suggestions, please open an issue
on `GitHub <https://github.com/j4321/Scheduler/issues>`_.



.. |Linux| image:: https://img.shields.io/badge/platform-Linux-blue.svg
    :alt: Linux
.. |License| image:: https://img.shields.io/github/license/j4321/Scheduler.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.en.html
    :alt: License - GPLv3
