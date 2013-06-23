import sys, os, logging, time, orphilia, Queue

from shared import path_rewrite

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

configurationDirectory = orphilia.client.getConfigurationDirectory()

def monitor():
	class LoggingEventHandler(FileSystemEventHandler):
		"""Logs all the events captured."""

		def on_moved(self, event):
			super(LoggingEventHandler, self).on_moved(event)
			par = event.src_path
			path = par[len(dropboxPath)+1:]
			par2 = event.dest_path
			path2 = par2[len(dropboxPath)+1:]
			
			if os.name == "nt":
				path = path_rewrite.rewritepath('posix',path)
				path2 = path_rewrite.rewritepath('posix',path2)

			what = 'directory' if event.is_directory else 'file'
			if what == "file":
				tmp = [ 'mv', path, path2]
				queue.put(orphilia.client.client(tmp))
			else:
				tmp = [ 'mkdir', path2 ]
				queue.put(orphilia.client.client(tmp))
				tmp = [ 'rm', path ]
				queue.put(orphilia.client.client(tmp))
			logging.info(" > Moved %s: from %s to %s", what, event.src_path, event.dest_path)

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
						path = par[len(dropboxPath)+1:]
						tmp = [ 'put', dropboxPath + path, path2, 'add' ]
						queue.put(orphilia.client.client(tmp))
				else:
						par = event.src_path
						path = par[len(dropboxPath)+1:]
						if os.name == "nt":
							path = path_rewrite.rewritepath('posix',path)
						tmp = [ 'mkdir', path ]
						queue.put(orphilia.client.client(tmp))
				logging.info(" > Created %s: %s", what, event.src_path)
			else:
				what = 'directory' if event.is_directory else 'file'
				if what == 'directory':
					par = event.src_path
					path = par[len(dropboxPath)+1:]
					if os.name == "nt":
						path = path_rewrite.rewritepath('posix',path)
					tmp = [ 'mkdir', path ]
					queue.put(orphilia.client.client(tmp))
					logging.info(" > Created %s: %s", what, event.src_path)

		def on_deleted(self, event):
			super(LoggingEventHandler, self).on_deleted(event)
			par = event.src_path
			path = par[len(dropboxPath)+1:]
			if os.name == "nt":
				path = path_rewrite.rewritepath('posix',path)
			what = 'directory' if event.is_directory else 'file'
			tmp = [ 'rm', path ]
			queue.put(orphilia.client.client(tmp))
			logging.info(" > Deleted %s: %s", what, event.src_path)

		def on_modified(self, event):
			super(LoggingEventHandler, self).on_modified(event)

			what = 'directory' if event.is_directory else 'file'
			if what == "file":
				par = event.src_path
				path = par[len(dropboxPath)+1:]
				if os.name == "nt":
					path = path_rewrite.rewritepath('posix',path)
				if os.name <> "nt":
					tmp = [ 'rm', path ]
					queue.put(orphilia.client.client(tmp))
				while True:
					size1 = os.path.getsize(par)
					time.sleep(0.2)
					size2 = os.path.getsize(par)
					if size1 == size2:
						break
				tmp = [ 'put', dropboxPath + '/' + path, path, 'upd']
				queue.put(orphilia.client.client(tmp))
			logging.info(" > Modified %s: %s", what, event.src_path)

	dropboxPath = orphilia.client.getDropboxPath()

	logging.basicConfig(level=logging.INFO,
						format='%(message)s',
						datefmt='%Y-%m-%d %H:%M:%S')
	event_handler = LoggingEventHandler()
	observer = Observer()
	queue = Queue.Queue(0)
	observer.schedule(event_handler, dropboxPath, recursive=True)
	observer.start()
	try:
	  while True:
		time.sleep(1)
		statusf = open(os.path.normpath(configurationDirectory+'/net-status'), 'r')
		status = statusf.read()
		statusf.close()
		if status == "1":
		   exit()
	  while not q.empty():
		print q.get()
	except KeyboardInterrupt:
	  observer.stop()
	  observer.join()
