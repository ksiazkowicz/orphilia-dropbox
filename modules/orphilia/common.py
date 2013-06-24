import os, sys

def getConfigurationDirectory():
	home = os.path.expanduser('~')
	if sys.platform[:5] == 'haiku':
		configurationDirectory = os.path.normpath(home + '/config/settings/Orphilia/')
	elif sys.platform[:3] == 'win':
		configurationDirectory = os.path.normpath(home + '/AppData/Roaming/Orphilia/')
	else:
		configurationDirectory = os.path.normpath(home + '/.orphilia/')
	return configurationDirectory

configurationDirectory = getConfigurationDirectory()

def putIn(string,filename,method):
	if method == "append":
		putInFile = open(filename,"a")
	else:
		putInFile = open(filename,"w")
	putInFile.write(string)
	putInFile.close
	
def orphiliaNotify(method,string):
	if notifier != '':
		os.system(notifier + ' ' + method + ' \"'+ string + '\"')

def getDropboxPath():
	try:
		open(os.path.normpath(configurationDirectory+'/dropbox-path'), 'r')
	except:
		print(' ! Dropbox folder path not specified. Run configuration utility')
		dropboxPath = os.path.normpath(os.path.expanduser('~') + '/Dropbox')
	else:
		dropboxPathSetting = open(os.path.normpath(configurationDirectory+'/dropbox-path'), 'r')
		dropboxPath = dropboxPathSetting.read()
		dropboxPathSetting.close()
	return dropboxPath

def getAccountUID():
	try:
		open(os.path.normpath(configurationDirectory+'/dropbox-id'), 'r')
	except:
		print(' ! Account UID unknown. Public links won\'t work. Run configuration utility')
		dropboxUID = 0
	else:
		dropboxUIDSetting = open(os.path.normpath(configurationDirectory+'/dropbox-id'), 'r')
		dropboxUID = dropboxUIDSetting.read()
		dropboxUIDSetting.close()
	return dropboxUID

def getNotifier():
	try:
		open(os.path.normpath(configurationDirectory+'/notify-settings'), 'r')
	except:
		print(' ! Notifier not specified. Run configuration utility')
		notifier = ''
	else:
		notifierSetting = open(os.path.normpath(configurationDirectory+'/notify-settings'), 'r')
		notifier = notifierSetting.read()
		notifierSetting.close()
	return notifier
