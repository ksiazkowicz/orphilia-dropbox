import dropbox
import sys, os, json, re

APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'app_folder'

STATE_FILE = 'copy_between_accounts.json'

def main():
    if APP_KEY == '' or APP_SECRET == '':
        sys.stderr.write("ERROR: Set your APP_KEY and APP_SECRET at the top of %r.\n" % __file__)
        sys.exit(1)

    prog_name = sys.argv[0]
    args = sys.argv[1:]
    if len(args) == 0:
        sys.stderr.write("Usage:\n")
        sys.stderr.write("   %s link                                   Link to a user's account.  Also displays UID.\n" % prog_name)
        sys.stderr.write("   %s list                                   List linked users including UID..\n" % prog_name)
        sys.stderr.write("   %s copy '<uid>:<path>' '<uid>:<path>'     Copies a file from the first user's path, to the second user's path.\n" % prog_name)
        sys.stderr.write("\n   <uid> is the account UID shown when linked.  <path> is a path to a file on that user's dropbox.\n")
        exit(0)

    command = args[0]
    if command == 'link':
        command_link(args)
    elif command == 'list':
        command_list(args)
    elif command == 'copy':
        command_copy(args)
    else:
        sys.stderr.write("ERROR: Unknown command: \"%s\"" % command)
        sys.stderr.write("Run with no arguments for help.")
        exit(1)



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
    c = dropbox.client.DropboxClient(sess)
    account_info = c.account_info()

    sys.stdout.write("Link successful. %s is uid %s\n" % (account_info['display_name'], account_info['uid']))

    state = load_state()
    state[account_info['uid']] = {
                    'access_token' : [access_token.key, access_token.secret],
                    'display_name' : account_info['display_name'],
    }

    save_state(state)

def command_list(args):
    if len(args) != 1:
        sys.stderr.write("ERROR: \"list\" doesn't take any arguments\n")
        exit(1)

    state = load_state()
    for e in state.keys():
        sys.stdout.write("%s is uid %s\n" % (state[e]['display_name'], e))

def command_copy(args):
    if len(args) != 3:
        sys.stderr.write("ERROR: \"copy\" takes exactly two arguments")
        exit(1)

    state = load_state()

    if len(state.keys()) < 2:
        sys.stderr.write("ERROR: You can't use the copy command until at least two users have linked")
        exit(1)

    from_ = re.sub("['\"]", '', args[1])
    to_ = re.sub("['\"]", '', args[2])

    if not to_.count(':') or not from_.count(':'):
        sys.stderr.write("ERROR: Ill-formated paths. Run copy_between_accounts without arugments to see documentation.\n")
        exit(1)

    from_uid, from_path = from_.split(":")
    to_uid, to_path = to_.split(":")

    if not to_uid in state or not from_uid in state:
        sys.stderr.write("ERROR: Those UIDs have not linked.  Run with the \"list\" option to see linked UIDs.\n")
        exit(1)

    from_token = state[from_uid]['access_token']
    to_token = state[to_uid]['access_token']

    from_session = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    to_session = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

    from_session.set_token(*from_token)
    to_session.set_token(*to_token)

    from_client = dropbox.client.DropboxClient(from_session)
    to_client = dropbox.client.DropboxClient(to_session)

    # Create a copy ref under the identity of the from user
    copy_ref = from_client.create_copy_ref(from_path)['copy_ref']

    metadata = to_client.add_copy_ref(copy_ref, to_path)

    sys.stdout.write("File successly copied from %s to %s!\n" % (state[from_uid]['display_name'], state[to_uid]['display_name']))
    sys.stdout.write("The file now exists at %s\n" % metadata['path'])


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    f = open(STATE_FILE, 'r')
    state = json.load(f)
    f.close()
    return state

def save_state(state):
    f = open(STATE_FILE, 'w')
    json.dump(state, f, indent=4)
    f.close()

if __name__ == '__main__':
    main()
