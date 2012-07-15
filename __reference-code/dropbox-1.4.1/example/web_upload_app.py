import BaseHTTPServer
import cgi
import inspect
import urllib
import urlparse
import sys

from Cookie import SimpleCookie
from dropbox import session, client

# XXX Fill in your consumer key and secret below
# You can find these at http://www.dropbox.com/developers/apps
APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'app_folder' # should be 'dropbox' or 'app_folder' as configured for your app

HOST = None # override this if the server complains about missing Host headers
TOKEN_STORE = {}

def get_session():
    return session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

def get_client(access_token):
    sess = get_session()
    sess.set_token(access_token.key, access_token.secret)
    return client.DropboxClient(sess)

class ExampleHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def index_page(self):
        sess = get_session()
        request_token = sess.obtain_request_token()
        TOKEN_STORE[request_token.key] = request_token

        callback = "http://%s/callback" % (self.host)
        url = sess.build_authorize_url(request_token, oauth_callback=callback)
        prompt = """Click <a href="%s">here</a> to link with Dropbox."""
        return prompt % url

    def callback_page(self, oauth_token=None):
        # note: the OAuth spec calls it 'oauth_token', but it's
        # actually just a request_token_key...
        request_token_key = oauth_token
        if not request_token_key:
            return "Expected a request token key back!"

        sess = get_session()
        request_token = TOKEN_STORE[request_token_key]
        access_token = sess.obtain_access_token(request_token)
        TOKEN_STORE[access_token.key] = access_token

        self.set_cookie('access_token_key', access_token.key)
        return self.redirect('/upload')

    def upload_page(self):
        access_token_key = self.get_cookie('access_token_key')
        access_token = TOKEN_STORE.get(access_token_key)
        if not access_token:
            return self.redirect('/')

        if self.method == 'GET':
            return """
Upload a file!<br/>
<form enctype="multipart/form-data" method="post" action="/upload">
    <input type="file" name="file"/><br/>
    <input type="submit"/>
</form>
"""

        if self.method == 'POST':
            file = self.get_upload()
            db = get_client(access_token)
            result = db.put_file('/' + file.filename, file.file)

            dest_path = result['path']
            url_args = urllib.urlencode({'dest_path': dest_path})
            return self.redirect("/success?" + url_args)

    def success_page(self, dest_path=None):
        msg = "Success! Your file was uploaded to your Dropbox account as %s."
        return msg % dest_path



    # "Pay no attention to that man behind the curtain!"
    #
    # Below this point is code the web framework of your choice should
    # supply for you. Consider it a quick and (really) dirty micro-framework.
    def set_cookie(self, key, value):
        self.cookies[key] = value

    def get_cookie(self, key):
        in_cookies = SimpleCookie()
        request_cookies = self.headers.get('Cookie')
        if request_cookies:
            in_cookies.load(request_cookies)
            val = in_cookies.get(key)
            return val.value if val else None
        return None

    def get_upload(self):
        environ = {'REQUEST_METHOD': self.method}
        fs = cgi.FieldStorage(self.rfile, self.headers, environ=environ)
        return fs['file']

    def redirect(self, dest):
        self.send_response(302)
        self.send_header("Location", dest)

        return "Redirecting to %s..." % dest

    def request(method):
        def handler(self):
            self.method = method
            self.cookies = SimpleCookie()
            self.host = self.headers.get('Host') or HOST
            if not self.host:
                err = "Set HOST in web_example.py so we can redirect back."
                self.send_error(500, err)
                return

            parsed = urlparse.urlparse(self.path)
            route = parsed.path[1:] or 'index'
            args = dict(cgi.parse_qsl(parsed.query))
            page = getattr(self, route + '_page', None)

            if not page:
                self.send_error(404, "Route %s not found" % self.path)
                return

            page_args = inspect.getargspec(page)[0]
            for k in args.keys():
                if k not in page_args:
                    del args[k]

            result = page(**args)

            if result:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                if len(self.cookies):
                    self.wfile.write(self.cookies.output() + '\r\n')
                self.end_headers()
                self.wfile.write(result)

        return handler

    do_GET = request('GET')
    do_POST = request('POST')

def main():
    if APP_KEY == '' or APP_SECRET == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    if len(sys.argv) == 1:
        print "usage: python web_example.py [PORT]"

    port = sys.argv[1] if len(sys.argv) > 1 else "8000"
    print "Browse to http://localhost:%s to try this app." % port
    BaseHTTPServer.test(ExampleHandler, BaseHTTPServer.HTTPServer)

if __name__ == '__main__':
    main()
