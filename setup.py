#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
import os


images = [os.path.join("schedulerlib/images/", img) for img in os.listdir("schedulerlib/images/")]
sounds = [os.path.join("schedulerlib/sounds/", s) for s in os.listdir("schedulerlib/sounds/")]

data_files = [("/usr/share/pixmaps", ["scheduler.svg", "scheduler-tray.svg"]),
              ("/usr/share/doc/scheduler", ["README.rst", "changelog"]),
              ("/usr/share/man/man1", ["scheduler.1.gz"]),
              ("/usr/share/scheduler/images/", images),
              ("/usr/share/scheduler/sounds/", sounds),
              ("/usr/share/applications", ["scheduler.desktop"])]
for loc in os.listdir('schedulerlib/locale'):
    data_files.append(("/usr/share/locale/{}/LC_MESSAGES/".format(loc),
                       ["schedulerlib/locale/{}/LC_MESSAGES/scheduler.mo".format(loc)]))


with open("schedulerlib/version.py") as f:
    exec(f.read())

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(name='scheduler',
      version=__version__,
      description='Alarms and reminders',
      long_description=long_description,
      url='https://github.com/j4321/Scheduler',
      author='Juliette Monsel',
      author_email='j_4321@protonmail.com',
      license='GPLv3',
      classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
      ],
      data_files=data_files,
      keywords=['tkinter', 'tasks', 'scheduling'],
      packages=['schedulerlib', 'schedulerlib.trayicon', 'schedulerlib.widgets',
                'schedulerlib.settings'],
      package_data={'schedulerlib': ['packages.tcl']},
      scripts=["scheduler"],
      install_requires=["APScheduler", "Pillow", "ewmh", "matplotlib", "numpy"])
