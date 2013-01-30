from __future__ import with_statement

import contextlib
import itertools
import mock
import os
import pkg_resources
import ssl
import sys
import tempfile
import threading
import time
import traceback
import unittest
import urllib

try:
    import json
except ImportError:
    import simplejson as json

from wsgiref.simple_server import make_server, WSGIServer

try:
    from urlparse import parse_qs
except Exception:
    from cgi import parse_qs

from dropbox.rest import RESTClientObject, SDK_VERSION, ErrorResponse, ProperHTTPSConnection
from dropbox.six import b

SERVER_CERT_FILE = pkg_resources.resource_filename(__name__, 'server.crt')
SERVER_KEY_FILE = pkg_resources.resource_filename(__name__, 'server.key')

def clean_qs(d):
    return dict((k, v[0] if len(v) == 1 else v) for (k, v) in d.iteritems())

def json_dumpb(data):
    toret = json.dumps(data)
    if sys.version_info >= (3,):
        toret = toret.encode('utf8')
    return toret

class TestProperHTTPSConnection(unittest.TestCase):
    @contextlib.contextmanager
    def listen_server(self, routes):
        HOST = "localhost"
        PORT = 8080

        def catch_exception(call):
            def new(*n, **kw):
                try:
                    call()
                except Exception:
                    traceback.print_exc()
            return new

        can_connect = threading.Event()

        @catch_exception
        def run_thread():
            time_to_die = [False]
            def simple_app(environ, start_response):
                path = environ['PATH_INFO']

                if path == '/die':
                    time_to_die[0] = True
                    start_response('200 OK', [('Content-type', 'text/plain')])
                    return [b('dead')]

                try:
                    result = routes[path]
                except KeyError:
                    start_response('404 NOT FOUND', [('Content-type', 'text/plain')])
                    return [b('NOT FOUND')]
                else:
                    start_response('200 OK', [('Content-type', 'text/plain')])
                    print "returning!", result
                    return [result]

            class SecureWSGIServer(WSGIServer):
                def get_request(self):
                    socket, client_address = WSGIServer.get_request(self)
                    socket = ssl.wrap_socket(socket,
                                             server_side=True,
                                             certfile=SERVER_CERT_FILE,
                                             keyfile=SERVER_KEY_FILE,
                                             ssl_version=ssl.PROTOCOL_TLSv1)
                    return socket, client_address

            server = make_server(HOST, PORT, simple_app, server_class=SecureWSGIServer)
            try:
                can_connect.set()
                while not time_to_die[0]:
                    server.handle_request()
            finally:
                server.server_close()

        t = threading.Thread(target=run_thread)
        t.start()
        try:
            a = ProperHTTPSConnection(HOST, PORT, trusted_cert_file=SERVER_CERT_FILE)
            can_connect.wait()
            yield a
        finally:
            a.close()
            try:
                urllib.urlopen("https://localhost:8080/die").close()
            except Exception:
                traceback.print_exc()
            t.join()

    def test_basic(self):
        path = "/"
        result = b("sup")
        with self.listen_server({path : result}) as a:
            a.connect()
            a.request("GET", path)
            response = a.getresponse()
            self.assertEqual(response.read(), result)

    def test_basic_unicode(self):
        path = u"/\u4545"
        result = b("sup")
        with self.listen_server({path : result}) as a:
            a.connect()
            # URLs can't have unicode in them,
            # they have to be quoted by urllib.quote
            with self.assertRaises(Exception):
                a.request("GET", path)

class TestGet(unittest.TestCase):
    def test_basic(self):
        json_data = {'foo' : 'bar', 'baz' : 42}
        url = 'https://api.dropbox.com/metadata'

        # setup mocks
        response = mock.Mock()
        response.status = 200
        response.read.return_value = json_dumpb(json_data)

        conn = mock.Mock()
        conn.getresponse.return_value = response

        mock_http_connect = mock.Mock()
        mock_http_connect.return_value = conn

        # invoke code
        ret = RESTClientObject(http_connect=mock_http_connect).GET(url)

        # check code
        mock_http_connect.assert_called_with('api.dropbox.com', 443)
        conn.request.assert_called_with('GET', url, None,
                                        {'User-Agent' : 'OfficialDropboxPythonSDK/' + SDK_VERSION})
        conn.getresponse.assert_called_with()
        response.read.assert_called_with()

        self.assertEqual(ret, json_data)

    def test_non_200(self):
        json_data = {'error' : 'bar', 'user_error' : 42}
        url = 'https://api.dropbox.com/metadata'
        reason = 1
        status = 304
        headers = {'sup' : 'there'}
        body = json_dumpb(json_data)

        # setup mocks
        response = mock.Mock()
        response.status = status
        response.read.return_value = body
        response.reason = reason
        response.getheaders.return_value = headers

        conn = mock.Mock()
        conn.getresponse.return_value = response

        mock_http_connect = mock.Mock()
        mock_http_connect.return_value = conn

        # invoke code
        try:
            RESTClientObject(http_connect=mock_http_connect).GET(url)
        except ErrorResponse, e:
            self.assertEqual(e.status, 304)
            self.assertEqual(e.error_msg, json_data['error'])
            self.assertEqual(e.user_error_msg, json_data['user_error'])
            self.assertEqual(e.reason, reason)
            self.assertEqual(e.headers, headers)
            self.assertEqual(e.body, body)

        # check code
        mock_http_connect.assert_called_with('api.dropbox.com', 443)
        conn.request.assert_called_with('GET', url, None,
                                        {'User-Agent' : 'OfficialDropboxPythonSDK/' + SDK_VERSION})
        conn.getresponse.assert_called_with()
        response.read.assert_called_with()

    def test_crazy_unicode(self):
        json_data = {'foo' : 'bar', 'baz' : 42}
        url = u'https://api.dropbox.com/metadata\u4545\u6f22/\u8a9e'

        # setup mocks
        response = mock.Mock()
        response.status = 200
        response.read.return_value = json_dumpb(json_data)

        conn = mock.Mock()
        conn.getresponse.return_value = response

        mock_http_connect = mock.Mock()
        mock_http_connect.return_value = conn

        # invoke code
        ret = RESTClientObject(http_connect=mock_http_connect).GET(url)

        # check code
        mock_http_connect.assert_called_with('api.dropbox.com', 443)
        conn.request.assert_called_with('GET', url, None,
                                        {'User-Agent' : 'OfficialDropboxPythonSDK/' + SDK_VERSION})
        conn.getresponse.assert_called_with()
        response.read.assert_called_with()

        self.assertEqual(ret, json_data)

class TestPost(unittest.TestCase):
    def test_basic(self):
        json_data = {'foo' : 'bar', 'baz' : 42}
        url = 'https://api.dropbox.com/metadata'

        # setup mocks
        response = mock.Mock()
        response.status = 200
        response.read.return_value = json_dumpb(json_data)

        conn = mock.Mock()
        conn.getresponse.return_value = response

        mock_http_connect = mock.Mock()
        mock_http_connect.return_value = conn

        # invoke code
        ret = RESTClientObject(http_connect=mock_http_connect).POST(url)

        # check code
        mock_http_connect.assert_called_with('api.dropbox.com', 443)
        conn.request.assert_called_with('POST', url, None,
                                        {'User-Agent' : 'OfficialDropboxPythonSDK/' + SDK_VERSION})
        conn.getresponse.assert_called_with()
        response.read.assert_called_with()

        self.assertEqual(ret, json_data)

    def _post_params(self, params):
        json_data = {'foo' : 'bar', 'baz' : 42}
        url = 'https://api.dropbox.com/metadata'
        post_params = params

        # setup mocks
        response = mock.Mock()
        response.status = 200
        response.read.return_value = json_dumpb(json_data)

        conn = mock.Mock()
        conn.getresponse.return_value = response

        mock_http_connect = mock.Mock()
        mock_http_connect.return_value = conn

        # invoke code
        ret = RESTClientObject(http_connect=mock_http_connect).POST(url, params=post_params)

        # check code
        mock_http_connect.assert_called_with('api.dropbox.com', 443)
        conn.request.assert_called_with('POST', url, mock.ANY,
                                        {'User-Agent' : 'OfficialDropboxPythonSDK/' + SDK_VERSION,
                                         'Content-type' : 'application/x-www-form-urlencoded'})
        self.assertEqual(clean_qs(parse_qs(conn.request.call_args[0][2])),
                         post_params)

        conn.getresponse.assert_called_with()
        response.read.assert_called_with()

        self.assertEqual(ret, json_data)

    def test_post_params(self):
        self._post_params({'quux' : 'is', 'a' : 'horse'})

    def test_post_params_crazy_unicode_values(self):
        # Python 2 can't handle unicode in the key name
        self._post_params({u'quux' : 'is\u4545', 'a' : 'horse\u4545'})

class TestPut(unittest.TestCase):
    def test_body(self):
        json_data = {'foo' : 'bar', 'baz' : 42}
        url = 'https://api.dropbox.com/metadata'
        post_params = {'quux' : 'is', 'a' : 'horse'}

        # setup mocks
        response = mock.Mock()
        response.status = 200

        conn = mock.Mock()
        conn.getresponse.return_value = response

        mock_http_connect = mock.Mock()
        mock_http_connect.return_value = conn

        fd, path = tempfile.mkstemp()
        os.unlink(path)
        with os.fdopen(fd, 'wb+') as f:
            f.writelines(itertools.repeat(b("a5"), int(16 * 1024 / 2)))
            f.seek(0)

            # invoke code
            ret = RESTClientObject(http_connect=mock_http_connect).PUT(url, body=f,
                                                                       raw_response=True)

            # check code
            mock_http_connect.assert_called_with('api.dropbox.com', 443)
            conn.request.assert_called_with('PUT', url, "",
                                            {'User-Agent' : 'OfficialDropboxPythonSDK/' + SDK_VERSION,
                                             'Content-Length' : str(16 * 1024)})
            sent = b('').join(a[0][0] for a in conn.send.call_args_list)
            self.assertEqual(sent, b("a5") * int(16 * 1024 / 2))

            conn.getresponse.assert_called_with()
            assert ret is response
