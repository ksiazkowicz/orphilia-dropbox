# An example use of the /delta API call.  Maintains a local cache of
# the App Folder's contents.  Use the 'update' sub-command to update
# the local cache.  Use the 'find' sub-command to search the local
# cache.
#
# Example usage:
#
# 1. Link to your Dropbox account
#    > python search_cache.py link
#
# 2. Go to Dropbox and make changes to the contents.
#
# 3. Update the local cache to match what's on Dropbox.
#    > python search_cache.py update
#
# 4. Search the local cache.
#    > python search_cache.py find 'txt'
#
# Repeat steps 2-4 any number of times.

import dropbox
import sys, os, json

APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'app_folder'

STATE_FILE = 'search_cache.json'

def main():
    # Lets us print unicode characters through sys.stdout/stderr
    reload(sys).setdefaultencoding('utf8')

    if APP_KEY == '' or APP_SECRET == '':
        sys.stderr.write("ERROR: Set your APP_KEY and APP_SECRET at the top of %r.\n" % __file__)
        sys.exit(1)

    prog_name = sys.argv[0]
    args = sys.argv[1:]

    if len(args) == 0:
        sys.stderr.write("Usage:\n")
        sys.stderr.write("   %s link           Link to a user's account.\n" % prog_name)
        sys.stderr.write("   %s update         Update cache to the latest on Dropbox.\n" % prog_name)
        sys.stderr.write("   %s update <num>   Update cache, limit to <num> pages of /delta.\n" % prog_name)
        sys.stderr.write("   %s find <term>    Search the cache for <term> (case-sensitive).\n" % prog_name)
        sys.stderr.write("   %s find           Display entire cache.\n" % prog_name)
        sys.stderr.write("   %s reset          Delete the cache.\n" % prog_name)
        sys.exit(0)

    command = args[0]
    if command == 'link':
        command_link(args)
    elif command == 'update':
        command_update(args)
    elif command == 'find':
        command_find(args)
    elif command == 'reset':
        command_reset(args)
    else:
        sys.stderr.write("ERROR: Unknown command: %r\n" % command)
        sys.stderr.write("Run with no arguments for help.\n")
        sys.exit(1)

def command_link(args):
    if len(args) != 1:
        sys.stderr.write("ERROR: \"link\" doesn't take any arguments.\n")
        sys.exit(1)

    sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    request_token = sess.obtain_request_token()

    # Make the user log in and authorize this token
    url = sess.build_authorize_url(request_token)
    sys.stdout.write("1. Go to: %s\n" % url)
    sys.stdout.write("2. Authorize this app.\n")
    sys.stdout.write("After you're done, press ENTER.\n")
    raw_input()

    # This will fail if the user didn't visit the above URL and hit 'Allow'
    access_token = sess.obtain_access_token(request_token)
    sys.stdout.write("Link successful.\n")

    save_state({
        'access_token': (access_token.key, access_token.secret),
        'tree': {}
    })

def command_update(args):
    if len(args) == 1:
        page_limit = None
    elif len(args) == 2:
        page_limit = int(args[1])
    else:
        sys.stderr.write("ERROR: \"update\" takes either zero or one argument.\n")
        sys.exit(1)

    # Load state
    state = load_state()
    access_token = state['access_token']
    cursor = state.get('cursor')
    tree = state['tree']

    # Connect to Dropbox
    sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    sess.set_token(*access_token)
    c = dropbox.client.DropboxClient(sess)

    page = 0
    changed = False
    while (page_limit is None) or (page < page_limit):
        # Get /delta results from Dropbox
        result = c.delta(cursor)
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

def command_find(args):
    if len(args) == 1:
        term = ''
    elif len(args) == 2:
        term = args[1]
    else:
        sys.stderr.write("ERROR: \"find\" takes either zero or one arguments.\n")
        sys.exit(1)

    state = load_state()
    results = []
    search_tree(results, state['tree'], term)
    for r in results:
        sys.stdout.write("%s\n" % (r,))
    sys.stdout.write("[Matches: %d]\n" % (len(results),))

def command_reset(args):
    if len(args) != 1:
        sys.stderr.write("ERROR: \"reset\" takes no arguments.\n")
        sys.exit(1)

    # Delete cursor, empty tree.
    state = load_state()
    if 'cursor' in state:
        del state['cursor']
    state['tree'] = {}
    save_state(state)


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
        sys.stdout.write('+ %s\n' % path)
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
        sys.stdout.write('- %s\n' % path)
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

if __name__ == '__main__':
    main()
