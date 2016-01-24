import sys, os, shutil, random, cmd, locale, pprint, shlex, json, Queue, datetime, time
from shared import path_rewrite
from orphilia import common
import traceback
from os.path import exists, normpath, join, dirname
from dateutil.parser import parse, tz

####################### initialize Dropbox API #
################################################
###############################################
from dropbox import client, rest, session

APP_KEY = 'ij4b7rjc7tsnlj4'
APP_SECRET = '00evf045y00ml2e'
ACCESS_TYPE = 'dropbox'
SDK_VERSION = "2.0"

# check if I specified app_key and app_secret	
if APP_KEY == '' or APP_SECRET == '':
    exit(' x You need to set your APP_KEY and APP_SECRET!')

############### read settings, get things done #
################################################
###############################################

configurationDirectory = common.getConfigurationDirectory()

dropboxPath = common.getDropboxPath()
accountUID = common.getAccountUID()
notifier = common.getNotifier()

delta_switch = 0
STATE_FILE = normpath(configurationDirectory + '/search_cache.json')


################### initialize Dropbox session #
################################################
###############################################
# a wrapper around DropboxSession that stores a token to a file on disk
# (from Dropbox cli_client.py example)
class StoredSession(session.DropboxSession):
    TOKEN_FILE = normpath(configurationDirectory + "/token_store.txt")

    def load_creds(self):
        print(" > Loading access token..."),
        try:
            stored_creds = open(self.TOKEN_FILE).read()
            self.set_token(*stored_creds.split('|'))
            print(" [OK]")
        except IOError:
            print(" [FAILED]")
            print(" x Access token not found. Beginning new session.")
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

        # display authentication URL
        # might be enhanced with cool GUI stuff in the future
        print("url:" + url),
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
    queue = Queue.Queue(0)
    path, metadata = e
    branch, leaf = split_path(path.encode("utf-8"))

    if metadata is not None:
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
            print(' + ' + metadata['path'])

            # Only create an empty folder if there isn't one there already.
            if not node.is_folder():
                node.content = {}
            if delta_switch == 0:
                try:
                    os.makedirs(dropboxPath + "/" + metadata['path'])
                    print(" > Directory created.")
                except:
                    pass
        else:
            node.content = metadata['size'], metadata['modified']
            tmp = ['sync', node.path]
            directory = normpath(join(dropboxPath, dirname(node.path)))

            print(' + ' + node.path)

            if delta_switch == 0:
                try:
                    if not exists(directory): os.makedirs(directory)
                    queue.put(client(tmp))
                except Exception, err:
                    print(" x Something went wrong. Unable to get file.")
                    traceback.print_exc()
    else:
        print(' - ' + path.encode("utf-8"))
        if delta_switch == 0:
            try:
                queue.put(os.remove(dropboxPath + '/' + path))
            except:
                print(' x Something went wrong. Unable to remove element.')

        # Traverse down the tree until we find the parent of the entry we
        # want to delete.
        children = root
        for part in branch:
            node = children.get(part)
            # If one of the parent folders is missing, then we're done.
            if node is None or not node.is_folder():
                try:
                    queue.put(shutil.rmtree(dropboxPath + path))
                except:
                    print(' x Something went wrong. Unable to remove path')
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
        file = open(to_file, "w")

        if 'contents' in resp:
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1]
                file.write(('%s\n' % name).encode(encoding))
        file.close()

    if cmd == "share":
        param = parameters[1]
        f = api_client.share(param)
        url = str(f['url'])
        print(" > Generated link: " + url)

    elif cmd == "delta":
        state = load_state()
        cursor = state.get('cursor')
        tree = state['tree']
        page = 0
        changed = False
        page_limit = 15

        try:
            delta_switch = parameter[1]
        except:
            delta_switch = 0

        while (page_limit is None) or (page < page_limit):
            # Make an int for progress/total
            progress = 0
            total = 0
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
                total = total + 1
            for delta_entry in result['entries']:
                changed = True
                progress = progress + 1
                print("Current entry: " + str(progress) + "/" + str(total))
                apply_delta(tree, delta_entry)
                cursor = result['cursor']
                #if not result['has_more']: break

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
        notify = parameters[3]  # it can be 'add' or 'upd'

        from_file = open(os.path.expanduser(from_path), 'rb')
        # try:
        api_client.put_file("/" + to_path, from_file)
        # except:
        #	print(" x Unable to upload file. ")
        common.orphiliaNotify(notify, from_path)

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
        path = path_rewrite.rewritepath('posix', parameters[1])
        try:
            api_client.file_delete("/" + path)
            common.orphiliaNotify('rm', path)
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
        f = api_client.account_info()
        uid = str(f['uid'])
        return uid

    elif cmd == "get":
        from_path = parameters[1]
        to_path = parameters[2]

        resp = api_client.metadata(from_path)
        modified = resp['client_mtime']

        try:
            open(os.path.expanduser(to_path), 'rb')
        except:
            pass

        date1 = time.mktime(parse(modified).timetuple())
        f = api_client.get_file("/" + from_path)
        dirname = os.path.dirname(os.path.abspath(to_path))

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        file = open(to_path, "wb")
        try:
            file.write(f.read())
            file.close()
            os.utime(os.path.normpath(to_path), (date1, date1))
        except:
            print(" x Unable to save file.")

    elif cmd == "sync":
        """
        Command which syncs files.
            - if both file exists, compare the dates:
                - local is older? download from server
                - local is newer? remove from server and upload local
            - if only local exists, upload
            - if exists only on the server, download
        """
        # get path that was sent to client
        path = parameters[1]
        localPath = os.path.normpath(dropboxPath + '/' + path)
        # assume that both files actually exist
        change = 'upd'

        # check if file exists on the server, try to get response data
        try:
            resp = api_client.metadata(path)
            modified = resp['client_mtime']
            dropboxTime = parse(modified)
        except:
            # ok, it doesn't, so we're going to upload that file
            dropboxTime = 0
            change = 'add'

        # check if local file exists and try to get it's modified date
        try:
            localTime = datetime.datetime.fromtimestamp(os.path.getmtime(localPath), tz=tz.tzutc())
        except:
            change = 'get'
            localTime = 0

        # uhm, this was not supposed to happen...
        if dropboxTime == 0 and localTime == 0:
            print(" x WTF?! It looks like there is no file on the server nor locally...")
            exit()
        else:
            if change == "upd":
                # both file exists, decide what's next
                if localTime < dropboxTime:
                    # local file is older, download from server
                    change = "get"
                else:
                    # local file is newer, remove from server
                    tmp = ['rm', path]
                    client(tmp)
                    # and reupload
                    change = "add"

            # push tasks to client
            if change == "get":
                tmp = ['get', path, localPath]
                client(tmp)
            elif change == "add":
                tmp = ['put', localPath, path, change]
                client(tmp)

    print(" > Command '" + parameters[0] + "' executed")


def getPublicLink(parameters):
    par = parameters[0]
    link = 'https://dl.dropboxusercontent.com/u/' + accountUID + '/' + path_rewrite.rewritepath('url', par[len(
        os.path.normpath(dropboxPath + "/Public")) + 1:])
    common.orphiliaNotify('link', link)
    print(link)
