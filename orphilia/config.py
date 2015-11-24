import sys, os, shutil
from orphilia import common
from ConfigParser import SafeConfigParser

home = os.path.expanduser('~')

# set configurationDirectory path dependent from platform
configurationDirectory = common.getConfigurationDirectory()


def config():
    # remove old settings
    if os.path.isdir(configurationDirectory):
        shutil.rmtree(configurationDirectory)

        # create directory
    os.makedirs(configurationDirectory)
    print(
        "Welcome to Orphilia, an open-source crossplatform Dropbox client.\nIn few steps, you will configure your Dropbox account to be used with Orphilia.")

    # initialize config parser
    config = SafeConfigParser()
    config.read(configurationDirectory + '/config.ini')

    # make sure sections are there
    config.add_section('main')
    config.add_section('notifications')

    # if we're on Haiku, we'd like to use that cool script which pushes notifications to desktop
    if sys.platform[:5] == "haiku":
        notifier = 'orphilia_haiku-notify'
    else:
        # nope, just ask the user
        notifier = raw_input("Enter notify method: ")
        config.set('notifications', 'notifier', notifier)

    dropboxPath = raw_input("Dropbox folder location (optional):")

    if dropboxPath == "":
        dropboxPath = os.path.normpath(home + '/Dropbox')
    else:
        pass  # save dropbox path
    config.set('main', 'path', dropboxPath)

    # create directories if needed
    if not os.path.exists(dropboxPath):
        os.makedirs(dropboxPath)

    import orphiliaclient

    # create request for UID
    uid = orphiliaclient.client.client(['uid'])
    config.set('main', 'uid', uid)

    with open(configurationDirectory + '/config.ini', 'w') as f:
        config.write(f)

    print("Configuration files has been created.")
