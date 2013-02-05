import sys
import os
import logging
import time
import orphilia

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

home = os.path.expanduser('~')

# set configurationdir path dependent from platform
if sys.platform[:5] == "haiku":
	configurationdir = os.path.normpath(home + '/config/settings/Orphilia/')
elif sys.platform[:3] == 'win':
	configurationdir = os.path.normpath(home + '/AppData/Roaming/Orphilia/')
else:
	configurationdir = os.path.normpath(home + '/.orphilia/')

def monitor():
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
                 tmp = { 'mv', path, path2}
                 orphilia.client.orphilia_client(tmp)
            else:
                 tmp = { 'mkdir', path2 }
                 orphilia.client.orphilia_client(tmp)
                 tmp = { 'rm', path }
                 orphilia.client.orphilia_client(tmp)
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
                            tmp = { 'put', droppath + path, path }
                            orphilia.client.orphilia_client(tmp)
                    else:
                            par = event.src_path
                            path = par[len(droppath)+1:]
                            print('orphilia --client--silent \"mkdir \'' + path + '\'\"')
                            tmp = { 'mkdir', path}
                            orphilia.client.orphilia_client(tmp)
                    logging.info("Created %s: %s", what, event.src_path)
            else:
                    what = 'directory' if event.is_directory else 'file'
                    if what == 'directory':
                            par = event.src_path
                            path = par[len(droppath)+1:]
                            tmp = { 'mkdir', path}
                            orphilia.client.orphilia_client(tmp)
                            logging.info("Created %s: %s", what, event.src_path)

        def on_deleted(self, event):
            super(LoggingEventHandler, self).on_deleted(event)
            par = event.src_path
            path = par[len(droppath)+1:]
            what = 'directory' if event.is_directory else 'file'
            tmp = { 'rm', path }
            orphilia.client.orphilia_client(tmp)
            logging.info("Deleted %s: %s", what, event.src_path)

        def on_modified(self, event):
            super(LoggingEventHandler, self).on_modified(event)

            what = 'directory' if event.is_directory else 'file'
            if what == "file":
               par = event.src_path
               path = par[len(droppath)+1:]
               if os.name <> "nt":
                  tmp = { 'rm', 'path'}
                  orphilia.client.orphilia_client(tmp)
               tmp = { 'upd', droppath + '/' + path, path}
               orphilia.client.orphilia_client(tmp)
            logging.info("Modified %s: %s", what, event.src_path)

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
