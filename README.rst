Scheduler - Task scheduling and calendar
========================================
|Linux| |License|

System tray application for Linux to schedule events with possibity to set reminders.
It also provides the following desktop widgets:

- a calendar to display and add events
- the list of the week's events
- a list of tasks
- a timer
- a pomodoro timer (https://en.wikipedia.org/wiki/Pomodoro_Technique) recording statistics


Install
-------

Archlinux
~~~~~~~~~

    Scheduler is available in `AUR <https://aur.archlinux.org/packages/scheduler>`__.

Ubuntu
~~~~~~

    Scheduler is available in the PPA `ppa:j-4321-i/ppa <https://launchpad.net/~j-4321-i/+archive/ubuntu/ppa>`__.

    ::

        $ sudo add-apt-repository ppa:j-4321-i/ppa
        $ sudo apt-get update
        $ sudo apt-get install scheduler

Source code
~~~~~~~~~~~

    `mpg123 <https://sourceforge.net/projects/mpg123/files/mpg123/>`_, Python 3 and
    the following librairies:

         - Tkinter (Python wrapper for Tk)
         - `ewmh <https://pypi.python.org/pypi/ewmh>`_
         - `Pillow <https://pypi.python.org/pypi/Pillow>`_
         - `APScheduler <https://pypi.python.org/pypi/apscheduler>`_
         - `Matplotlib <https://matplotlib.org/>`_
         - `Numpy <https://www.numpy.org/>`_
         - `Babel <https://pypi.python.org/pypi/babel>`_
         - `tkcalendar <https://pypi.python.org/pypi/tkcalendar>`_
         - `python-dateutil <https://pypi.python.org/pypi/python-dateutil>`_

    It is also necessary to have at least one of the following GUI toolkits for the system tray icon:

         - `Tktray <https://code.google.com/archive/p/tktray/downloads>`_
         - `PyGTK <http://www.pygtk.org/downloads.html>`_
         - PyQt5, PyQt4 or PySide

    Optional dependencies:

        - libnotify and a notification server if your desktop environment does not provide one.
          (see https://wiki.archlinux.org/index.php/Desktop_notifications for more details): reminders as notifications
        - `tkcolorpicker <https://pypi.python.org/pypi/tkcolorpicker>`_ or zenity: nicer color chooser

    Install:

    ::

        $ sudo python3 setup.py install

    Scheduler can then be launched from *Menu > Utility > Scheduler* or directly from the command line with `scheduler`.


Troubleshooting
---------------


Current day highlighting in the calendar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The current day is highlighted in the calendar widget and updated every day at midnight if the computer is running.
    However, if the computer is in standby, the current day will not be updated. 
    You can either perform the update manually with

    ::
        
        $ scheduler -U
        
    or you can put the file `<scheduler@.service>`_ in */usr/lib/systemd/system* (already done for the Archlinux and Ubuntu packages) and enable the service:

    ::

        $ sudo systemctl enable scheduler@$USER

System tray icon
~~~~~~~~~~~~~~~~

    Several gui toolkits are available to display the system tray icon, so if the
    icon does not behave properly, try to change toolkit, they are not all fully
    compatible with every desktop environment.

Widget disappearance
~~~~~~~~~~~~~~~~~~~~

    If the widgets disappear when you click on them, open the setting dialog 
    from the menu and check the box 'Check this box if the widgets disappear 
    when you click'.


If you encounter bugs or if you have suggestions, please open an issue
on `GitHub <https://github.com/j4321/Scheduler/issues>`_.

.. |Linux| image:: https://img.shields.io/badge/platform-Linux-blue.svg
    :alt: Linux
.. |License| image:: https://img.shields.io/github/license/j4321/Scheduler.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.en.html
    :alt: License - GPLv3
