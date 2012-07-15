import sys
import os
import shutil
import logging

import locale
import pprint
import shlex

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

home = os.path.expanduser('~')

if sys.platform[:5] == "haiku":
	configurationdir = os.path.normpath(home + '/config/settings/Orphilia/')
else:
	configurationdir = os.path.normpath(home + '/.orphilia/')

def monitor():
    read_details = open(os.path.normpath(configurationdir+'/dropbox-path'), 'r')
    droppath = read_details.read()
    read_details.close()

    logging.basicConfig(level=logging.INFO,
                        format='%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, droppath, recursive=True)
    observer.start()
    try:
      while True:
        time.sleep(1)
        statusf = open(os.path.normpath(configurationdir+'/net-status'), 'r')
        status = statusf.read()
        statusf.close()
        if status == "1":
           exit()
    except KeyboardInterrupt:
      observer.stop()
      observer.join()

    class LoggingEventHandler(FileSystemEventHandler):
        """Logs all the events captured."""

        def on_moved(self, event):
            super(LoggingEventHandler, self).on_moved(event)
            par = event.src_path
            path = par[len(droppath)+1:]
            par2 = event.dest_path
            path2 = par2[len(droppath)+1:]

            what = 'directory' if event.is_directory else 'file'
            if what == "file":
                 os.system('orphilia --client--silent \"mv \\"' + path + '\\" \\"' + path2 + '\\"\"')
            else:
                 os.system('orphilia --client--silent \"mkdir \'' + path2 + '\'\"')
                 os.system('orphilia --client--silent \"rm \'' + path + '\'\"')
            logging.info("Moved %s: from %s to %s", what, event.src_path,
                         event.dest_path)

        def on_created(self, event):
            super(LoggingEventHandler, self).on_created(event)
            if os.name <> "nt":
                    what = 'directory' if event.is_directory else 'file'
                    if what == 'file':
                            par = event.src_path
                            while True:
                                  size1 = os.path.getsize(par)
                                  time.sleep(0.5)
                                  size2 = os.path.getsize(par)
                                  if size1 == size2:
                                     break
                            path = par[len(droppath)+1:]
                            os.system('orphilia --client--silent \"put \\"' + droppath +"/"+ path + '\\" \\"' + path + '\\"\"')
                    else:
                            par = event.src_path
                            path = par[len(droppath)+1:]
                            print('orphilia --client--silent \"mkdir \'' + path + '\'\"')
                            os.system('orphilia --client--silent \"mkdir \'' + path + '\'\"')
                    logging.info("Created %s: %s", what, event.src_path)
            else:
                    what = 'directory' if event.is_directory else 'file'
                    if what == 'directory':
                            par = event.src_path
                            path = par[len(droppath)+1:]
                            os.system('orphilia --client--silent \"mkdir \'' + path + '\'\"')
                            logging.info("Created %s: %s", what, event.src_path)

        def on_deleted(self, event):
            super(LoggingEventHandler, self).on_deleted(event)
            par = event.src_path
            path = par[len(droppath)+1:]
            what = 'directory' if event.is_directory else 'file'
            os.system('orphilia --client--silent \"rm \'' + path + '\'\"')
            logging.info("Deleted %s: %s", what, event.src_path)

        def on_modified(self, event):
            super(LoggingEventHandler, self).on_modified(event)

            what = 'directory' if event.is_directory else 'file'
            if what == "file":
               par = event.src_path
               path = par[len(droppath)+1:]
               if os.name <> "nt":
                  os.system('orphilia --client--silent \"rm \'' + path + '\'\"')
               os.system('orphilia --client--silent \"upd \'' + droppath +"/"+ path + '\' \'' + path + '\'\"')
            logging.info("Modified %s: %s", what, event.src_path)
