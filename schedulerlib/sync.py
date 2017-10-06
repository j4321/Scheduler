#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Scheduler - Sticky notes/post-it
Copyright 2016-2017 Juliette Monsel <j_4321@protonmail.com>

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


Sync note with server
"""


import easywebdav
import traceback
import os
import shutil
from schedulerlib.messagebox import showerror, SyncConflict
from schedulerlib.constants import CONFIG, DATA_PATH, DATA_INFO_PATH, JOBSTORE, save_modif_info


def _(text):
    return text


# --- WebDav
def sync_conflict(remote_path, local_path, webdav, exists_remote_info, text=None):
    """ handle sync conflict. Return the chosen action. """
    if text:
        ask = SyncConflict(text=text)
    else:
        ask = SyncConflict()
    ask.wait_window(ask)
    action = ask.get_action()
    if action == "download":
        webdav.download(remote_path, local_path)
        if exists_remote_info:
            webdav.download(remote_path + ".info", local_path + ".info")
    elif action == "upload":
        webdav.upload(local_path, remote_path)
        webdav.upload(local_path + ".info", remote_path + ".info")
    return action


def download_from_server(password):
    """ Try to download data from server, return True if it worked. """
    print('\n\nsync\n')
    remote_path = CONFIG.get("Sync", "file")
    remote_info_path = remote_path + ".info"
    remote_jobstore = remote_path + ".sqlite"
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            print(1)
            exists_remote_info = webdav.exists(remote_info_path)
            print(DATA_PATH)
            if os.path.exists(DATA_PATH):
                print(2)
                exists_local_info = os.path.exists(DATA_INFO_PATH)
                if exists_local_info:
                    with open(DATA_INFO_PATH) as fich:
                        tps_local = float(fich.readlines()[1])
                else:
                    tps_local = os.path.getmtime(DATA_PATH)
                    save_modif_info(tps_local)
                if exists_remote_info:
                    webdav.download(remote_info_path, "/tmp/scheduler.info")
                    with open("/tmp/scheduler.info") as fich:
                        tps_remote = float(fich.readlines()[1])
                    print(3, int(tps_remote) // 60, int(tps_local) // 60)
                    if int(tps_remote) // 60 >= int(tps_local) // 60:
                        print('download')
                        # file is more recent on server
                        webdav.download(remote_path, DATA_PATH)
                        webdav.download(remote_jobstore, JOBSTORE)
                        shutil.move("/tmp/scheduler.info", DATA_INFO_PATH)
                        return True
                    else:
                        res = sync_conflict(remote_path, DATA_PATH,
                                            webdav, exists_remote_info,
                                            text=_("Local data is more recent than on server. What do you want to do?"))
                        return res != ""
                else:
                    res = sync_conflict(remote_path, DATA_PATH, webdav, False)
                    return res != ""

            else:
                print(4)
                # no local data: download remote data
                webdav.download(remote_path, DATA_PATH)
                webdav.download(remote_jobstore, JOBSTORE)
                if exists_remote_info:
                    webdav.download(remote_info_path, DATA_INFO_PATH)
                return True
        else:
            print(5)
            # first sync
            return True
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
        return False
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return False


def upload_to_server(password, last_sync_time):
    """ upload data to server. """
    remote_path = CONFIG.get("Sync", "file")
    remote_info_path = remote_path + ".info"
    remote_jobstore = remote_path + ".sqlite"
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            exists_remote_info = webdav.exists(remote_info_path)
            save_modif_info()
            with open(DATA_INFO_PATH) as fich:
                info_local = fich.readlines()
            if exists_remote_info:
                webdav.download(remote_info_path, "/tmp/scheduler.info")
                with open("/tmp/scheduler.info") as fich:
                    info_remote = fich.readlines()
                if info_local[0] != info_remote[0] and last_sync_time // 60 < float(info_remote[1]) // 60:
                    # there was an update from another computer in the mean time
                    sync_conflict(remote_path, DATA_PATH, webdav, exists_remote_info)
                else:
                    webdav.upload(DATA_PATH, remote_path)
                    webdav.upload(JOBSTORE, remote_jobstore)
                    webdav.upload(DATA_INFO_PATH, remote_info_path)
            else:
                sync_conflict(remote_path, DATA_PATH, webdav, False)
#            setlocale(LC_ALL, 'C')
#            mtime_server = time.mktime(time.strptime(webdav.ls(remote_path)[0].mtime + time.strftime("%z"),
#                                                     "%a, %d %b %Y %X GMT%z"))
#            mtime_local = time.gmtime(os.path.getmtime(DATA_PATH))
#            mtime_local = time.strftime('%a, %d %b %Y %X GMT', mtime_local)
#            mtime_local = time.mktime(time.strptime(mtime_local, '%a, %d %b %Y %X GMT'))
#            if mtime_local // 60 - mtime_server // 60 >= -1:
#                # local file is more recent than remote one
#                webdav.upload(DATA_PATH, remote_path)
#            else:
#                ask = SyncConflict()
#                ask.wait_window(ask)
#                action = ask.get_action()
#                if action == "download":
#                    webdav.download(remote_path, DATA_PATH)
#                elif action == "upload":
#                    webdav.upload(DATA_PATH, remote_path)
        else:
            # first sync
            webdav.upload(DATA_PATH, remote_path)
            webdav.upload(JOBSTORE, remote_jobstore)
            webdav.upload(DATA_INFO_PATH, remote_info_path)
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
    except FileNotFoundError:
        showerror(_("Error"),
                  _("Local data not found.\n" + traceback.format_exc()))
    except Exception:
        showerror(_("Error"), traceback.format_exc())


def check_login_info(password):
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        webdav.exists(CONFIG.get("Sync", "file"))
        return True
    except easywebdav.OperationFailed as e:
        if e.actual_code == 401:
            showerror(_("Error"), _("Wrong login information."))
            return False
        else:
            err = str(e).splitlines()
            message = err[0] + "\n" + err[-1].split(":")[-1].strip()
            showerror(_("Error"), message)
            return False
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return False


def warn_exist_remote(password):
    """ When sync is activated, if a remote note file exists, it will
        be erased when the local file will be sync when app is closed. So
        warn user and ask him what to do.
    """
    remote_path = CONFIG.get("Sync", "file")
    webdav = easywebdav.connect(CONFIG.get("Sync", "server"),
                                username=CONFIG.get("Sync", "username"),
                                password=password,
                                protocol=CONFIG.get("Sync", "protocol"),
                                port=CONFIG.get("Sync", "port"),
                                verify_ssl=True)
    try:
        if webdav.exists(remote_path):
            ls = webdav.ls(remote_path)
            if len(ls) == 1:
                # it's a file
                remote_info_path = remote_path + '.info'
                ex = webdav.exists(remote_info_path)
                action = sync_conflict(remote_path, DATA_PATH, webdav, ex,
                                       _("The file {filename} already exists on the server.\
\nWhat do you want to do?").format(filename=remote_path))
                return action
            else:
                # it's a folder
                remote_path = os.path.join(remote_path, 'scheduler')
                CONFIG.set("Sync", "file", remote_path)
                if webdav.exists(remote_path):
                    remote_info_path = remote_path + '.info'
                    ex = webdav.exists(remote_info_path)
                    action = sync_conflict(remote_path, DATA_PATH, webdav, ex,
                                           _("The file {filename} already exists on the server.\
\nWhat do you want to do?").format(filename=remote_path))
                    return action
                else:
                    return "upload"
        else:
            return "upload"
    except easywebdav.OperationFailed as e:
        err = str(e).splitlines()
        message = err[0] + "\n" + err[-1].split(":")[-1].strip()
        showerror(_("Error"), message)
        return "error"
    except Exception:
        showerror(_("Error"), traceback.format_exc())
        return "error"
