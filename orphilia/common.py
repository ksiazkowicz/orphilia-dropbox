import os, sys
from ConfigParser import SafeConfigParser


def getConfigurationDirectory():
    home = os.path.expanduser('~')
    if sys.platform[:5] == 'haiku':
        configurationDirectory = os.path.normpath(home + '/config/settings/Orphilia/')
    elif sys.platform[:3] == 'win':
        configurationDirectory = os.path.normpath(home + '/AppData/Roaming/Orphilia/')
    else:
        configurationDirectory = os.path.normpath(home + '/.orphilia/')
    return configurationDirectory


def getNotifier():
    config = SafeConfigParser()
    config.read(configurationDirectory + '/config.ini')
    try:
        notifier = config.get('notifications', 'notifier')
    except:
        print(' ! Notifier not specified. Run configuration utility')
        notifier = ''
    return notifier


configurationDirectory = getConfigurationDirectory()
notifier = getNotifier()


def orphiliaNotify(method, string):
    if notifier != '':
        os.system(notifier + ' ' + method + ' \"' + string + '\"')


def getDropboxPath():
    config = SafeConfigParser()
    config.read(configurationDirectory + '/config.ini')
    try:
        dropboxPath = config.get('main', 'path')
    except:
        print(' ! Dropbox folder path not specified. Run configuration utility')
        dropboxPath = ''
    return dropboxPath


def getAccountUID():
    config = SafeConfigParser()
    config.read(configurationDirectory + '/config.ini')
    try:
        dropboxUID = config.get('main', 'uid')
    except:
        print(' ! Account UID unknown. Public links won\'t work. Run configuration utility')
        dropboxUID = ''
    return dropboxUID
