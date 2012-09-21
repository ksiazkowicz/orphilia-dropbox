import sys
import os
import random

import cmd
import locale
import pprint
import shlex
import json

from dropbox import client, rest, session
from shared import date_rewrite, path_rewrite

# wartosci moralne, a raczej parametry wszelakie
APP_KEY = 'ij4b7rjc7tsnlj4'
APP_SECRET = '00evf045y00ml2e'
ACCESS_TYPE = 'dropbox'
SDK_VERSION = "1.4"

home = os.path.expanduser('~')

if sys.platform[:5] == "haiku":
	configurationdir = os.path.normpath(home + '/config/settings/Orphilia/')
else:
	configurationdir = os.path.normpath(home + '/.orphilia/')
STATE_FILE = os.path.normpath(configurationdir + '/search_cache.json')

def putin(string,filename,method):
	if method == "append":
		putinfile = open(filename,"a")
	else:
		putinfile = open(filename,"w")
	putinfile.write(string)
	putinfile.close
	
def orphilia_notify(method,string):
	f = open(os.path.normpath(configurationdir + '/notify-settings'), 'r')
	notifier = f.read()
	f.close
	os.system(notifier + ' ' + method + ' \"'+ string + '\"')

###### DELTA UJEMNA I INNE TRAGEDIE
############################
############################

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
    path, metadata = e
    branch, leaf = split_path(path)

    if metadata is not None:
        print '+ %s\n' % path
        # Traverse down the tree until we find the parent folder of the entry
        # we want to add.  Create any missing folders along the way.
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
        else:
            node.content = metadata['size'], metadata['modified']
    else:
        print '- %s\n' % path
        # Traverse down the tree until we find the parent of the entry we
        # want to delete.
        children = root
        for part in branch:
            node = children.get(part)
            # If one of the parent folders is missing, then we're done.
            if node is None or not node.is_folder(): break
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
                results.append('%s  (%s, %s)' % (path, size, modified))
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
######################## TU ZACZYNA SIE KLIENT!

def orphilia_client():
	statusf = open(os.path.normpath(configurationdir+'/net-status'), 'r')
	status = statusf.read()
	statusf.close()
	if status == "1":
		exit()
	read_details = open(os.path.normpath(configurationdir+'/dropbox-path'), 'r')
	droppath = read_details.read()
	read_details.close()

	def command(login_required=True):
	    def decorate(f):
	        def wrapper(self, args):
	            if login_required and not self.sess.is_linked():
	                self.stdout.write("Please 'login' to execute this command\n")
	                return
	
	            try:
	                return f(self, *args)
	            except TypeError, e:
	                self.stdout.write(str(e) + '\n')
	            except rest.ErrorResponse, e:
	               msg = e.user_error_msg or str(e)
	               self.stdout.write('Error: %s\n' % msg)
	               msg2 = msg[:5]
	               if msg2 == "[401]":
		               print(" > Token problem. Unlinking..."),
		               self.sess.unlink()
		               print(" OK")
		               self.sess.link()
		               print(" > Repeating command...")
		               term = DropboxTerm(APP_KEY, APP_SECRET)
		               term.onecmd(sys.argv[2])
	
	        wrapper.__doc__ = f.__doc__
	        return wrapper
	    return decorate

	class DropboxTerm(cmd.Cmd):
	    def __init__(self, app_key, app_secret):
	        cmd.Cmd.__init__(self)
	        self.sess = StoredSession(app_key, app_secret, access_type=ACCESS_TYPE)
	        self.api_client = client.DropboxClient(self.sess)
	
	        self.sess.load_creds()

	    @command()
	    def do_delta(self):
	        state = load_state()
	        cursor = state.get('cursor')
	        tree = state['tree']
	        page = 0
	        changed = False
	        page_limit = 5
	        while (page_limit is None) or (page < page_limit):
	           # Get /delta results from Dropbox
	           result = self.api_client.delta(cursor)
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
	        print " > Command '" + sys.argv[2] + "' executed"

	    @command()
	    def do_ls(self,path, to_file):
	        resp = self.api_client.metadata(path)
	        file = open(to_file,"w")

	        if 'contents' in resp:
	            for f in resp['contents']:
	                name = os.path.basename(f['path'])
	                encoding = locale.getdefaultlocale()[1]
	                file.write(('%s\n' % name).encode(encoding))
	        file.close()
	        print " > Command '" + sys.argv[2] + "' executed"

	    @command()
	    def do_ls_alt(self, path, to_file):
	        resp = self.api_client.metadata(path)
		a = unicode(resp)
	        file = open(to_file,"w")
		print >> file, a
	        file.close()
	        print " > Command '" + sys.argv[2] + "' executed"

	    @command()
	    def do_sync_everything(self, path):
	        term = DropboxTerm(APP_KEY, APP_SECRET)
	        resp = self.api_client.metadata(path)
	        rand1 = random.random()
	        dirlist = os.listdir(droppath + "/" + path)
	        to_file = os.path.normpath(configurationdir + "_tmpscript" + str(rand1) + ".tmp")
	        file = open(to_file,"w")
	        file.write('orphilia --client--silent \"sync_folder \\"' + path + "/" + '\\"\"' + '\n')

	        for fname in dirlist:
	                if os.path.isdir(droppath + "/" + path + fname):
			        file.write('cd \"' + fname + '\"'+ '\n')
			        file.write('orphilia --client--silent \"sync_everything \\"' + path + "/" + fname + '\\"\"' + '\n')
			        file.write('cd ..'+ '\n')
	        file.close()
	        os.system("chmod +x " + to_file)
	        os.system("sh " + to_file)
	        os.system("rm " + to_file)
	        print " > Command '" + sys.argv[2] + "' executed"

	    @command()
	    def do_get(self, path, to_path):
	        resp = self.api_client.metadata(path)
	        modified = resp['modified']
	        date1 = modified[5:]
	        date1 = date_rewrite.generate_modifytime(date1)
	        f = self.api_client.get_file("/" + path)
	        file = open(to_path,"w")
		file.write(f.read())
	        file.close()
	        os.system("touch -d \"" + date1 + "\" \"" + to_path + "\"")
	        
	        print " > Command '" + sys.argv[2] + "' executed"

	    @command()
	    def do_sync_folder(self, path):
		term = DropboxTerm(APP_KEY, APP_SECRET)
	        """"""
	        resp = self.api_client.metadata(path)
	        dirlist = os.listdir(droppath + "/" + path)
	        rand1 = random.random()

	        if 'contents' in resp:
	            for f in resp['contents']:
		        name = os.path.basename(f['path'])
		        encoding = locale.getdefaultlocale()[1]
	                if ('%s' % name).encode(encoding) not in dirlist:
	                        print ('%s' % name).encode(encoding) + " not found."
		                if not os.path.isfile(('%s' % name).encode(encoding)):
				        dir = f['is_dir']
				        if not dir:
				                term.onecmd('get \"' + path + "/" + ('%s' % name).encode(encoding) + '\" \"' +  droppath + "/" + path +  ('%s' % name).encode(encoding) + '\"')
				        if dir:
				                os.system('mkdir \"' + droppath + "/" + path +  ('%s' % name).encode(encoding) + '\"')
	                else:
		                name = os.path.basename(f['path'])
		                encoding = locale.getdefaultlocale()[1]
	                        print ('%s' % name).encode(encoding) + " found. Checking..."

		                modified = f['modified']
		                date1 = modified[5:]
		                if os.path.isfile(('%s' % name).encode(encoding)):
				        t = time.ctime(os.path.getmtime(('%s' % name).encode(encoding)))
				        date2 = t[4:]

				        hour = str(int(hour) +1)

				        timestamp1_rnd = date_rewrite.generate_timestampd(date1)
				        print(date1 + " converted to " + timestamp1_rnd)
				        timestamp2_rnd = date_rewrite.generate_timestamp(date2)
				        print(date2 + " converted to " + timestamp2_rnd)
				        
			                dir = f['is_dir']

					if timestamp1_rnd < timestamp2_rnd:
				                if not dir:

						        print " - Dropbox verion of file \"" + ('%s' % name).encode(encoding) + "\" is older. Updating..."
						        term.onecmd('rm \"' +  path + "/" + ('%s' % name).encode(encoding) + '\"')
						        term.onecmd('sync \"' + ('%s' % name).encode(encoding) + '\" \"' +  path + "/" + ('%s' % name).encode(encoding) + '\"')
				                else:
						        print + " x " + name + " is directory. Skipping."

					elif timestamp1_rnd > timestamp2_rnd:
						  term.onecmd('get \"' + path + "/" + ('%s' % name).encode(encoding) + '\" \"' +  ('%s' % name).encode(encoding) + '\"')
					          print " - Dropbox verion of file \"" + ('%s' % name).encode(encoding) + "\" is newer. Updating."

					else:
					        print " x File \"" + ('%s' % name).encode(encoding) + "\" is identical. Skipping."
								      

		        print " > Command '" + sys.argv[2] + "' executed"
	
	    @command()
	    def do_logout(self):
	        self.sess.unlink()
	        print " > Unlinked ;("

	    @command()
	    def do_cat(self, path):
	        f = self.api_client.get_file("/" + path)
	        self.stdout.write(f.read())
	        self.stdout.write("\n")

	    @command()
	    def do_mkdir(self, path):
	        self.api_client.file_create_folder("/" + path)
	        print " > Directory \'" + path + "\' created"
	
	    @command()
	    def do_rm(self, path):
	        """delete a file or directory"""
	        self.api_client.file_delete("/" + path)
	        orphilia_notify('rm',path)

	    @command()
	    def do_mv(self, from_path, to_path):
	        """move/rename a file or directory"""
	        self.api_client.file_move("/" + from_path,
	                                  "/" + to_path)
	        print " > Command '" + sys.argv[2] + "' executed"
	
	    @command()
	    def do_account_info(self):
	        f = self.api_client.account_info()
	        pprint.PrettyPrinter(indent=2).pprint(f)
	        print " > Command '" + sys.argv[2] + "' executed"

	    @command()
	    def do_uid(self, parameter2):
	        f = self.api_client.account_info()
	        uid = str(f['uid'])
	        putin(uid,parameter2,'rewrite')
	        print " > UID updated"

	    @command()
	    def do_put(self, from_path, to_path):
	        from_file = open(os.path.expanduser(from_path))

	        self.api_client.put_file("/" + to_path, from_file)
	        orphilia_notify('add',from_path)

	    @command()
	    def do_upd(self, from_path, to_path):
	        from_file = open(os.path.expanduser(from_path))
	        
	        self.api_client.rm_file("/" + to_path)
	        self.api_client.put_file("/" + to_path, from_file)
	        orphilia_notify('upd',from_path)
	
	    # the following are for command line magic and aren't Dropbox-related
	    def emptyline(self):
	        pass

	    def do_EOF(self, line):
	        self.stdout.write('\n')
	        return True

	    def parseline(self, line):
	        parts = shlex.split(line)
	        if len(parts) == 0:
	            return None, None, line
	        else:
	            return parts[0], parts[1:], line


	class StoredSession(session.DropboxSession):
	    TOKEN_FILE = os.path.normpath(configurationdir + "/token_store.txt")

	    def load_creds(self):
	        print " > Loading access token...",
	        try:
	            stored_creds = open(self.TOKEN_FILE).read()
	            self.set_token(*stored_creds.split('|'))
	            print " OK"
	        except IOError:
	            print " FAILED"
	            print " x Access token not found. Beggining new session."
	            self.link()

	    def write_creds(self, token):
	        f = open(self.TOKEN_FILE, 'w')
	        f.write("|".join([token.key, token.secret]))
	        f.close()

	    def delete_creds(self):
	        os.unlink(self.TOKEN_FILE)
	
	    def link(self):
	        print " > Authorizing..."
	        request_token = self.obtain_request_token()
	        url = self.build_authorize_url(request_token)
	        if sys.platform[:5] == "haiku":
	              putin(url,os.path.normpath(configurationdir+'/authorize-url'),'rewrite')
	              drmchujnia = os.system("orphilia_haiku-authorize")
	              os.system('rm ' + os.path.normpath(configurationdir+'/authorize-url'))
	        else:
	              print "url:", url,
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

	if APP_KEY == '' or APP_SECRET == '':
	   exit('You need to set your APP_KEY and APP_SECRET!')
	term = DropboxTerm(APP_KEY, APP_SECRET)
	term.onecmd(sys.argv[2])
		
def client-verbose(cmd):
    reload(sys).setdefaultencoding('utf8')
    print('Orphilia')
    print('Maciej Janiszewski, 2010-2012]')
    print('based on Dropbox SDK from https://www.dropbox.com/developers/reference/sdk')
    print('')
    orphilia_client(cmd)

def public():
	read_details = open(os.path.normpath(configurationdir+'/dropbox-path'), 'r')
	DROPPATH = read_details.read()
	read_details.close()
	read_details2 = open(os.path.normpath(configurationdir+'/dropbox-id'), 'r')
	DROPID = read_details2.read()
	read_details2.close()
	par = sys.argv[2]
	link = 'http://dl.dropbox.com/u/' + DROPID + '/' + path_rewrite.rewritepath('url',par[len(os.path.normpath(DROPPATH + "/Public"))+1:])
	orphilia_notify('link',link)
