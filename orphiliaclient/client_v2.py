import sys, os, shutil, random, cmd, locale, pprint, shlex, json, Queue, datetime, time
from orphilia import common
from os.path import exists, normpath, join, dirname
from dateutil.parser import parse, tz
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect


class OAuth2Session:
    """
    Provides OAuth2 login and token store.
    """
    TOKEN_FILE = normpath(common.getConfigurationDirectory() + "/o2_store.txt")
    auth_flow = None
    access_token = ""
    user_id = ""

    def __init__(self, app_key="", app_secret=""):
        # prepare auth flow
        self.auth_flow = DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        self.load_creds()

    def link(self):
        authorize_url = self.auth_flow.start()
        print "1. Go to: " + authorize_url
        print "2. Click \"Allow\" (you might have to log in first)."
        print "3. Copy the authorization code."
        auth_code = raw_input("Enter the authorization code here: ").strip()

        try:
            self.access_token, self.user_id = self.auth_flow.finish(auth_code)
        except Exception, e:
            print('Error: %s' % (e,))
            return

        self.write_creds()

    def load_creds(self):
        print(" > Loading access token..."),
        try:
            stored_creds = open(self.TOKEN_FILE).read()
            self.access_token, self.user_id = stored_creds.split('|')
            print(" [OK]")
        except IOError:
            print(" [FAILED]")
            print(" x Access token not found. Beginning new session.")
            self.link()

    def write_creds(self):
        f = open(self.TOKEN_FILE, 'w')
        f.write("|".join([self.access_token, self.user_id]))
        f.close()
        print(" > Credentials written.")

    def delete_creds(self):
        os.unlink(self.TOKEN_FILE)
        print(" > Credentials removed.")

    def unlink(self):
        self.delete_creds()
        # I can't unlink the app yet properly (API limitation), so let's just remove the token


class OrphiliaClient:
    APP_KEY = 'ij4b7rjc7tsnlj4'
    APP_SECRET = '00evf045y00ml2e'
    SDK_VERSION = "2.0"

    configuration_directory = common.getConfigurationDirectory()
    dropbox_path = common.getDropboxPath()
    account_UID = common.getAccountUID()
    notifier = common.getNotifier()

    dropbox = None
    session = None

    def __init__(self):
        # check if I specified app_key and app_secret
        if self.APP_KEY == '' or self.APP_SECRET == '':
            exit(' x You need to set your APP_KEY and APP_SECRET!')

        # get Dropbox session
        self.session = OAuth2Session(self.APP_KEY, self.APP_SECRET)

        # initialize API client
        self.dropbox = dropbox.Dropbox(self.session.access_token)
        print(' > OrphiliaClient is ready.')

    def unlink(self):
        """
        Kills current Dropbox session. Returns nothing.
        """
        self.session.unlink()

    def ls(self):
        print self.dropbox.files_list_folder("")

    def get(self, path):
        """
        Downloads file from Dropbox to our Dropbox folder.
        :param path: path to file on Dropbox
        """
        # generate local path from dropbox_path and given path parameter
        local_path = os.path.normpath(self.dropbox_path + '/' + path)
        local_path_directory = os.path.dirname(os.path.abspath(local_path))

        try:
            # try to get metadata for file and it's bytes as well
            md, res = self.dropbox.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print(' x HTTP error', err)
            return False

        data = res.content
        print(" > File %s downloaded (%d bytes)" % (path, len(data)))

        # get modified date from metadata and convert it to timestamp
        modified_time = time.mktime(md.server_modified.timetuple())

        # check if directories exist
        if not os.path.exists(local_path_directory):
            print(" > Directories do not exist. Creating.")
            os.makedirs(local_path_directory)

        # open a file and try to write
        f = open(local_path, "wb")
        try:
            # save file contents
            f.write(data)
            f.close()
            # update modified time
            os.utime(os.path.normpath(local_path), (modified_time, modified_time))

            # check times (better safe than sorry
            local_time = os.path.getmtime(local_path)
            if local_time != modified_time:
                # ugh, seriously?
                print(" x Timestamp mismatch. local: %f != server: %f" % (local_time, modified_time))
                os.remove(local_path)
                raise Exception("Timestamp mismatch.")

            # yaaay, it worked!
            print(" > File saved properly.")
        except:
            print(" x Unable to save file.")
            return False

        # well, everything works, right?
        return True

    def remove(self, path):
        """
        Removes file from Dropbox.
        :param path: path to file on Dropbox
        """
        try:
            # try to move file (response will be metadata, probably)
            res = self.dropbox.files_delete(path)
        except dropbox.exceptions.HttpError as err:
            print(' x HTTP error', err)
            return False
        except dropbox.exceptions.ApiError as err:
            print(' x API error', err)
            return False

        # assume it worked
        return True

    def move(self, path, new_path):
        """
        Moves/renames files on Dropbox
        :param path: path to file on Dropbox
        :param new_path: new name/path
        """
        try:
            # try to move file (response will be metadata, probably)
            res = self.dropbox.files_move(path, new_path)
        except dropbox.exceptions.HttpError as err:
            print(' x HTTP error', err)
            return False
        except dropbox.exceptions.ApiError as err:
            print(' x API error', err)
            return False

        # assume it worked
        return True
