import sys, os, random, cmd, locale, pprint, shlex, json, Queue
from shared import date_rewrite, path_rewrite

print("""Orphilia
Maciej Janiszewski, 2010-2013
made with Dropbox SDK from https://www.dropbox.com/developers/reference/sdk \n""")

####################### initialize Dropbox API #
################################################
###############################################
from dropbox import client, rest, session
APP_KEY = 'ij4b7rjc7tsnlj4'
APP_SECRET = '00evf045y00ml2e'
ACCESS_TYPE = 'dropbox'
SDK_VERSION = "1.5"

# check if I specified app_key and app_secret	
if APP_KEY == '' or APP_SECRET == '':
	exit(' x You need to set your APP_KEY and APP_SECRET!')

############### read settings, get things done #
################################################
###############################################
def getConfigurationDirectory():
	home = os.path.expanduser('~')
	if sys.platform[:5] == 'haiku':
		configurationDirectory = os.path.normpath(home + '/config/settings/Orphilia/')
	elif sys.platform[:3] == 'win':
		configurationDirectory = os.path.normpath(home + '/AppData/Roaming/Orphilia/')
	else:
		configurationDirectory = os.path.normpath(home + '/.orphilia/')
	return configurationDirectory

configurationDirectory = getConfigurationDirectory()

def getDropboxPath():
	try:
		open(os.path.normpath(configurationDirectory+'/dropbox-path'), 'r')
	except:
		print(' ! Dropbox folder path not specified. Run configuration utility')
		dropboxPath = os.path.normpath(os.path.expanduser('~') + '/Dropbox')
	else:
		dropboxPathSetting = open(os.path.normpath(configurationDirectory+'/dropbox-path'), 'r')
		dropboxPath = dropboxPathSetting.read()
		dropboxPathSetting.close()
	return dropboxPath

def getAccountUID():
	try:
		open(os.path.normpath(configurationDirectory+'/dropbox-id'), 'r')
	except:
		print(' ! Account UID unknown. Public links won\'t work. Run configuration utility')
		dropboxUID = 0
	else:
		dropboxUIDSetting = open(os.path.normpath(configurationDirectory+'/dropbox-id'), 'r')
		dropboxUID = dropboxUIDSetting.read()
		dropboxUIDSetting.close()
	return dropboxUID

def getNotifier():
	try:
		open(os.path.normpath(configurationDirectory+'/notify-settings'), 'r')
	except:
		print(' ! Notifier not specified. Run configuration utility')
		notifier = ''
	else:
		notifierSetting = open(os.path.normpath(configurationDirectory+'/notify-settings'), 'r')
		notifier = notifierSetting.read()
		notifierSetting.close()
	return notifier

dropboxPath = getDropboxPath()
accountUID = getAccountUID()
notifier = getNotifier()

delta_switch = 0
STATE_FILE = os.path.normpath(configurationDirectory + '/search_cache.json')

##################### some internal procedures #
################################################
###############################################
def putIn(string,filename,method):
	if method == "append":
		putInFile = open(filename,"a")
	else:
		putInFile = open(filename,"w")
	putInFile.write(string)
	putInFile.close
	
def orphiliaNotify(method,string):
	if notifier != '':
		os.system(notifier + ' ' + method + ' \"'+ string + '\"')

################### initialize Dropbox session #
################################################
###############################################
# a wrapper around DropboxSession that stores a token to a file on disk
# (from Dropbox cli_client.py example)
class StoredSession(session.DropboxSession):
	TOKEN_FILE = os.path.normpath(configurationDirectory + "/token_store.txt")

	def load_creds(self):
		print(" > Loading access token..."),
		try:
			stored_creds = open(self.TOKEN_FILE).read()
			self.set_token(*stored_creds.split('|'))
			print(" OK")
		except IOError:
			print(" FAILED")
			print(" x Access token not found. Beggining new session.")
			self.link()

	def write_creds(self, token):
		f = open(self.TOKEN_FILE, 'w')
		f.write("|".join([token.key, token.secret]))
		f.close()

	def delete_creds(self):
		os.unlink(self.TOKEN_FILE)
	
	def link(self):
		print(" > Authorizing...")
		request_token = self.obtain_request_token()
		url = self.build_authorize_url(request_token)
		# some code to make this fancy window with URL show up in Haiku OS
		if sys.platform[:5] == "haiku":
			putIn(url,os.path.normpath(configurationDirectory+'/authorize-url'),'rewrite')
			os.system("orphilia_haiku-authorize")
			os.system('rm ' + os.path.normpath(configurationDirectory+'/authorize-url'))
		else:
			print("url:"+ url),
			raw_input()

		self.obtain_access_token(request_token)
		self.write_creds(self.token)

		save_state({
			'access_token': (request_token.key, request_token.secret),
			'tree': {}
		})

	def unlink(self):
		self.delete_creds()
		session.DropboxSession.unlink(self)

################### delta parsing related code #
################################################
###############################################
# We track the folder state as a tree of Node objects.
class Node(object):
	def __init__(self, path, content):
		# The "original" path (i.e. not the lower-case path)
		self.path = path
		# For files, content is a pair (size, modified)
		# For folders, content is a dict of children Nodes, keyed by lower-case file names.
		self.content = content
	def is_folder(self):
		return isinstance(self.content, dict)
	def to_json(self):
		return (self.path, Node.to_json_content(self.content))
	@staticmethod
	def from_json(jnode):
		path, jcontent = jnode
		return Node(path, Node.from_json_content(jcontent))
	@staticmethod
	def to_json_content(content):
		if isinstance(content, dict):
			return dict([(name_lc, node.to_json()) for name_lc, node in content.iteritems()])
		else:
			return content
	@staticmethod
	def from_json_content(jcontent):
		if isinstance(jcontent, dict):
			return dict([(name_lc, Node.from_json(jnode)) for name_lc, jnode in jcontent.iteritems()])
		else:
			return jcontent

def apply_delta(root, e):
	chleb = Queue.Queue(0)
	path, metadata = e
	branch, leaf = split_path(path)

	if metadata is not None:
		print(' + ' + path)
		# Traverse down the tree until we find the parent folder of the entry
		# we want to add. Create any missing folders along the way.
		children = root
		for part in branch:
			node = get_or_create_child(children, part)
			# If there's no folder here, make an empty one.
			if not node.is_folder():
				node.content = {}
			children = node.content

		# Create the file/folder.
		node = get_or_create_child(children, leaf)
		node.path = metadata['path']  # Save the un-lower-cased path.
		if metadata['is_dir']:
			# Only create an empty folder if there isn't one there already.
			if not node.is_folder():
				node.content = {}
			if delta_switch == 0:
				try:
					os.mkdir(dropboxPath + "/" + path)
				except:
					pass
		else:
			node.content = metadata['size'], metadata['modified']
			tmp = [ 'get', path, dropboxPath + "/" + path]
			if delta_switch == 0:
				try:
					chleb.put(client_new(tmp))
				except:
					print(" x Something went wrong")
	else:
		print(' - ' + path)
		if delta_switch == 0:
			try:
				chleb.put(os.remove(dropboxPath + '/' + path))
			except:
				print(' x Something went wrong')
	
		# Traverse down the tree until we find the parent of the entry we
		# want to delete.
		children = root
		for part in branch:
			node = children.get(part)
			# If one of the parent folders is missing, then we're done.
			if node is None or not node.is_folder(): 
				chleb.put(os.rmtree(dropboxPath+path)) 
				break
			children = node.content
		else:
			# If we made it all the way, delete the file/folder (if it exists).
			if leaf in children:
				del children[leaf]

def get_or_create_child(children, name):
	child = children.get(name)
	if child is None:
		children[name] = child = Node(None, None)
	return child

def split_path(path):
	assert path[0] == '/', path
	assert path != '/', path
	parts = path[1:].split('/')
	return parts[0:-1], parts[-1]

# Recursively search 'tree' for files that contain the string in 'term'.
# Print out any matches.
def search_tree(results, tree, term):
	for name_lc, node in tree.iteritems():
		path = node.path
		if (path is not None) and term in path:
			if node.is_folder():
				results.append('%s' % (path,))
			else:
				size, modified = node.content
				results.append('%s (%s, %s)' % (path, size, modified))
		# Recurse on children.
		if node.is_folder():
			search_tree(results, node.content, term)

def load_state():
	if not os.path.exists(STATE_FILE):
		sys.stderr.write("ERROR: Couldn't find state file %r.  Run the \"link\" subcommand first.\n" % (STATE_FILE))
		sys.exit(1)
	f = open(STATE_FILE, 'r')
	state = json.load(f)
	state['tree'] = Node.from_json_content(state['tree'])
	f.close()
	return state

def save_state(state):
	f = open(STATE_FILE, 'w')
	state['tree'] = Node.to_json_content(state['tree'])
	json.dump(state, f, indent=4)
	f.close()

#####################################################
###################################################
######################## Client-related code

print(' > Attempting authorization...')

# defines 'sess' and 'api_client' to simplify the code, also begins auth process
sess = StoredSession(APP_KEY, APP_SECRET, access_type=ACCESS_TYPE)
api_client = client.DropboxClient(sess)
sess.load_creds()

def client(parameters):
	cmd = parameters[0]
	
	if cmd == "ls":
		path = parameters[1]
		to_file = parameters[2]
			
		resp = api_client.metadata(path)
		file = open(to_file,"w")
		
		if 'contents' in resp:
			for f in resp['contents']:
				name = os.path.basename(f['path'])
				encoding = locale.getdefaultlocale()[1]
				file.write(('%s\n' % name).encode(encoding))
		file.close()
		
	elif cmd == "delta":
		state = load_state()
		cursor = state.get('cursor')
		tree = state['tree']
		page = 0
		changed = False
		page_limit = 5
		
		try:
			delta_switch = parameter[1]
		except:
			delta_switch = 0
		
		while (page_limit is None) or (page < page_limit):
			# Get /delta results from Dropbox
			result = api_client.delta(cursor)
			page += 1
			if result['reset'] == True:
				sys.stdout.write('reset\n')
				changed = True
				tree = {}
			cursor = result['cursor']
			# Apply the entries one by one to our cached tree.
			for delta_entry in result['entries']:
				changed = True
				apply_delta(tree, delta_entry)
				cursor = result['cursor']
				if not result['has_more']: break

		if not changed:
			sys.stdout.write('No updates.\n')
		else:
		# Save state
			state['cursor'] = cursor
			state['tree'] = tree
			save_state(state)
		
	elif cmd == "put":
		from_path = parameters[1]
		to_path = parameters[2]
		notify = parameters[3] # it can be 'add' or 'upd'
		
		from_file = open(os.path.expanduser(from_path), 'rb')
		#try:
		api_client.put_file("/" + to_path, from_file)
		#except:
		#	print(" x Unable to upload file. ")
		orphiliaNotify(notify,from_path)
		
	elif cmd == "unlink":
			sess.unlink()
			print(" > Unlinked :C")

	elif cmd == "cat":
		f = api_client.get_file("/" + path)
		stdout.write(f.read())
		stdout.write("\n")

	elif cmd == "mkdir":
		path = parameters[1]
		try:
			api_client.file_create_folder("/" + path)
		except:
			print(" x Unable to make directory " + path)
		print(" > Directory \'" + path + "\' created")
	
	elif cmd == "rm":
		path = path_rewrite.rewritepath('posix',parameters[1])
		try:
			api_client.file_delete("/" + path)
			orphiliaNotify('rm',path)
		except:
			print(" x Unable to remove file " + path)

	elif cmd == "mv":
		from_path = parameters[1]
		to_path = parameters[2]
		try:
			api_client.file_move("/" + from_path, "/" + to_path)
		except:
			print(" x Unable to move file " + from_path + " to " + to_path)
	
	elif cmd == "account_info":
		f = api_client.account_info()
		pprint.PrettyPrinter(indent=2).pprint(f)
		
	elif cmd == "uid":
		param = parameters[1]
		f = api_client.account_info()
		uid = str(f['uid'])
		try:
			putIn(uid,param,'rewrite')
		except:
			print(" x Unable to save file.")
		print(" > UID updated")
		
	elif cmd == "get":
		from_path = parameters[1]
		to_path = parameters[2]
		
		resp = api_client.metadata(from_path)
		modified = resp['modified']
		date1 = modified[5:]
		date1 = date_rewrite.generate_modifytime(date1)
		f = api_client.get_file("/" + from_path)
		file = open(to_path,"wb")
		try:
			file.write(f.read())
		except:
			print(" x Unable to save file.")
		file.close()
		os.system("touch -d \"" + date1 + "\" \"" + to_path + "\"") # this solution won't work on Windows
		
	elif cmd == "sync_folder":
		path = parameters[1]
		
		resp = api_client.metadata(path) # gets list of files in directory on Dropbox
		dirlist = os.listdir(dropboxPath + "/" + path) # gets list of files in directory on local computer
		rand1 = random.random() # generates random integer
		
		queue = Queue.Queue(0)
	
		if 'contents' in resp: # begin comparing both lists
			for f in resp['contents']:
				name = os.path.basename(f['path'])
				encoding = locale.getdefaultlocale()[1]
				if ('%s' % name).encode(encoding) not in dirlist: # found Dropbox file, which isn't present on local computer
					print ('%s' % name).encode(encoding) + " not found."
					if not os.path.isfile(('%s' % name).encode(encoding)):
						dir = f['is_dir']
						if not dir:
							tmp = [ 'get', path + "/" + name, dropboxPath + "/" + path + name]
							queue.put(client_new(tmp))
						if dir:
							os.mkdir(dropboxPath + "/" + path +  ('%s' % name).encode(encoding))
				else: # found Dropbox file which is present on local computer, check this out, bro!
					name = os.path.basename(f['path'])
					encoding = locale.getdefaultlocale()[1]
					print(('%s' % name).encode(encoding) + " found. Checking...")

	print(" > Command '" + parameters[0] + "' executed")
	
def getPublicLink(parameters):
	par = parameters[1]
	link = 'https://dl.dropboxusercontent.com/u/' + accountUID + '/' + path_rewrite.rewritepath('url',par[len(os.path.normpath(dropboxPath + "/Public"))+1:])
	orphiliaNotify('link',link)
