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

    sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

    if len(sys.argv) != 5:
        sys.stderr.write("Usage: %s <access-token> <access-secret> <file-to-upload> <cu-hash>\n" % sys.argv[0])
        sys.exit(1)

    sess.set_token(sys.argv[1], sys.argv[2])
    client = dropbox.client.DropboxClient(sess)

    file_path, cu_hash = sys.argv[3], sys.argv[4]

    camera_upload(client, cu_hash, file_path)

def camera_upload(client, cu_hash, file_path):
    file_obj = open(file_path)
    basename = os.path.basename(file_path)
    path = "/camera_upload/%s/%s" % (cu_hash, basename)

    url, params, headers = client.request(path, {}, method='PUT', content_server=True)
    r = dropbox.rest.RESTClient.PUT(url, file_obj, headers)
    file_obj.close()
    return r

if __name__ == '__main__':
    main()
