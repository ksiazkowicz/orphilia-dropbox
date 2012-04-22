
import httplib
import simplejson as json
import socket
import struct
import urllib
import urlparse
import os
import pkg_resources
import ssl
import shutil
import logging

import oauth.oauth as oauth

import re

import cmd
import locale
import pprint
import shlex
import sys
import random
import getpass
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

if len(sys.argv) > 1:
    wtd = sys.argv[1]
else:
    wtd = "brick"

