# module to take care of watching file changes and loading data from them

import os
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileClosedEvent
from threading import Timer


UPDATE_INTERVAL = 20

def load_dir_and_repeat(dirpath,callback,mtimes={}):
	for f in os.listdir(dirpath):
		if f.startswith('.'): continue
		fullpath = os.path.join(dirpath,f)

		mtime = os.stat(fullpath).st_mtime
		if mtimes.get(fullpath) != mtime:
			mtimes[fullpath] = mtime
			callback(fullpath)

	tim = Timer(UPDATE_INTERVAL,load_dir_and_repeat,args=(dirpath,callback,))
	tim.daemon = True
	tim.start()

def load_file_and_repeat(filepath,callback,mtimes={}):

	mtime = os.stat(filepath).st_mtime
	if mtimes.get(filepath) != mtime:
		mtimes[filepath] = mtime
		callback(filepath)

	tim = Timer(UPDATE_INTERVAL,load_file_and_repeat,args=(filepath,callback,))
	tim.daemon = True
	tim.start()



class Handler:
	def __init__(self,callback):
		self.callback = callback
	def dispatch(self,event):
		if isinstance(event,FileModifiedEvent) or isinstance(event,FileClosedEvent):
			if not os.path.basename(event.src_path).startswith('.'):
				#print("Importing",event.src_path)
				self.callback(event.src_path)

def observe_dir(dirpath,callback):
	if os.environ.get('USE_MANUAL_FS_POLLING'):
		load_dir_and_repeat(dirpath,callback)
	else:
		observer = Observer()
		observer.schedule(Handler(callback),dirpath,recursive=True)
		observer.start()

		# initial run
		for f in os.listdir(dirpath):
			if f.startswith('.'): continue
			fullpath = os.path.join(dirpath,f)

			callback(fullpath)

def observe_file(filepath,callback):
	if os.environ.get('USE_MANUAL_FS_POLLING'):
		load_file_and_repeat(filepath,callback)
	else:
		observer = Observer()
		observer.schedule(Handler(callback),filepath,recursive=False)
		observer.start()

		callback(filepath)
