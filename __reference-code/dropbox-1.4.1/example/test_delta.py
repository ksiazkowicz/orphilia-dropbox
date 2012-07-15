from dropbox import client, rest, session
import sys, os, json, time

APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'dropbox'

STATE_FILE = 'delta-state.'

def main():
    sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

    if len(sys.argv) == 3:
        sess.set_token(sys.argv[1], sys.argv[2])
    elif len(sys.argv) != 1:
        print "Either provide 0 or 2 arguments."
        sys.exit(1)
    else:
        request_token = sess.obtain_request_token()
        # Make the user log in and authorize this token
        url = sess.build_authorize_url(request_token)
        print "url:", url
        print "Authorize this app in your browser. After you're done, press enter."
        raw_input()

        # This will fail if the user didn't visit the above URL and hit 'Allow'
        access_token = sess.obtain_access_token(request_token)
        print "Access token: %s %s" % (access_token.key, access_token.secret)

    c = client.DropboxClient(sess)

    f = open(STATE_FILE + 'in', 'r')
    cursor, tree = json.load(f)
    f.close()

    dump = open(STATE_FILE + 'dump', 'w')

    print "Getting delta..."
    while True:
        start_time = time.clock()
        results = c.delta(cursor)
        elapsed = time.clock() - start_time
        print "Elapsed: %1.3f" % elapsed
        if results['reset']:
            tree = {}
        changes = results['entries']
        for change in changes:
            dump.write("%s\n" % json.dumps(change))
        cursor = results['cursor']
        print "  cursor: %r" % cursor
        for change in changes:
            apply_change(tree, change)
        if not results['has_more']: break

    dump.close()

    f = open(STATE_FILE + 'out', 'w')
    json.dump([cursor, tree], f)
    f.close()

    f = open('delta.tree', 'w')
    print_tree(f, tree)
    f.close()

    print "Recursive metadata..."
    rmd_tree = recursive_metadata(c, '/')

    f = open('rmd.tree', 'w')
    print_tree(f, rmd_tree)
    f.close()

    if rmd_tree != tree:
        print "NOT EQUAL!"
    else:
        print "equal"

def apply_change(root, change):
    tree = root
    path, md = change
    if md is not None:
        if md['is_dir']: md['sub'] = {}
        path = md['path']
        parts = path[1:].split('/')
        branch = parts[0:-1]
        leaf = parts[-1]
        md['name'] = leaf
        current_path = ''
        for part in branch:
            # If the dir isn't there, create it implicitly.
            if not tree.has_key(part.lower()):
                tree[part.lower()] = {'sub': {}}
            node = tree[part.lower()]
            if not node.has_key('sub'):
                print "---- TREE ----"
                print_tree(sys.stdout, root)
                print "---- DEL ----"
                print repr(path)
                raise Exception("Couldn't add: path is a child of a file.")
            tree = node['sub']
        if tree.has_key(leaf.lower()):
            node = tree[leaf.lower()]
            if node.has_key('sub'):
                if md.has_key('sub'):
                    # If it's a DIR on top of a DIR, preserve the children
                    md['sub'] = node['sub']
                elif len(node['sub']) > 0:
                    raise Exception("Couldn't add file on top of empty directory.")
        tree[leaf.lower()] = md
    else:
        parts = path[1:].split('/')
        branch = parts[0:-1]
        leaf = parts[-1]
        for part in branch:
            if not tree.has_key(part): return
            node = tree[part]
            if not node.has_key('sub'): return
            tree = node['sub']
        if not tree.has_key(leaf): return
        del tree[leaf]

def recursive_metadata(c, path):
    m = c.metadata(path, list=True)
    d = {}
    for entry in m['contents']:
        path = entry['path']
        if entry['is_dir']:
            entry['sub'] = recursive_metadata(c, path)
        name = path.split('/')[-1]
        d[name.lower()] = entry
        entry['name'] = name
    del m['contents']
    return d

def print_tree(out, tree, indent=''):
    for name, entry in sorted(tree.iteritems()):
        if not entry.has_key('name'):
            print "---- NO NAME: %r" % entry
        out.write('%s%r\n' % (indent, entry['name']))
        for key, value in sorted(entry.iteritems()):
            if key == 'sub': continue
            if key == 'name': continue
            if key == 'root': continue
            if key == 'icon': continue
            out.write("%s- %s = %r\n" % (indent, key, value))
        if entry.has_key('sub'):
            print_tree(out, entry['sub'], indent+'  ')

if __name__ == '__main__':
    main()
