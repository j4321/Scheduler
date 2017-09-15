#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
import os

images = [os.path.join("schedulerlib/images/", img) for img in os.listdir("schedulerlib/images/")]

data_files = [("/usr/share/pixmaps", ["scheduler.svg"]),
              ("/usr/share/doc/scheduler", ["README.rst"]),
              ("/usr/share/scheduler/images/", images),
              ("/usr/share/applications", ["scheduler.desktop"])]

with open("schedulerlib/version.py") as f:
    exec(f.read())

setup(name='scheduler',
      version=__version__,
      description='Alarms and reminders',
      long_description=""" Alarms and reminders """,
#      url='https://github.com/j4321/Scheduler',
      author='Juliette Monsel',
      author_email='j_4321@protonmail.com',
      license='GPLv3',
      classifiers=[
            'Development Status :: 4 - Beta',
            #'Intended Audience :: Developers',
#            'Topic :: Software Development :: Widget Sets',
#            'Topic :: Software Development :: Libraries :: Python Modules',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Natural Language :: English',
#            'Natural Language :: French',
            'Operating System :: POSIX :: Linux',
      ],
      data_files=data_files,
      keywords=['tkinter', 'tasks', 'scheduling'],
      packages=["schedulerlib"],
      scripts = ["scheduler"],
      requires=["os", "tkinter", "apscheduler", "pickle", "traceback", "sys"]
)
