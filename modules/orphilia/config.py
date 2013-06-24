import sys, os, shutil
from orphilia import common

home = os.path.expanduser('~')

# set configurationDirectory path dependent from platform
configurationDirectory = common.getConfigurationDirectory()

def config():
	if os.path.isdir(configurationDirectory):
		shutil.rmtree(configurationDirectory)
	os.makedirs(configurationDirectory)
	common.putIn('0',os.path.normpath(configurationDirectory+'/net-status'),'rewrite')
	print("Welcome to Orphilia, an open-source crossplatform Dropbox client.\nIn few steps, you will configure your Dropbox account to be used with Orphilia.")
	
	if sys.platform[:5] == "haiku":
		common.putIn('orphilia_haiku-notify',os.path.normpath(configurationDirectory+'/notify-settings'),'rewrite')

	else:
		notifier = raw_input("Enter notify method: ")
		common.putIn(notifier,os.path.normpath(configurationDirectory+'/notify-settings'),'rewrite')

	dropboxPath = raw_input("Dropbox folder location (optional):")
	
	if dropboxPath == "":	
		dropboxPath = os.path.normpath(home + '/Dropbox')
	else:
		pass
		
	common.putIn(dropboxPath,os.path.normpath(configurationDirectory+'/dropbox-path'),'rewrite')
	if not os.path.exists(dropboxPath):
 		os.makedirs(dropboxPath)

	print("Please wait. Orphilia is making configuration files.")
	
	import orphiliaclient
	
	tmp = [ 'uid', os.path.normpath(configurationDirectory+'/dropbox-id')]
	orphiliaclient.client.client(tmp)
	
	print("Configuration files has been created.")

def config_gui(parameters):
	dropboxPath = parameters[0]
	
	if os.path.isdir(configurationDirectory):
		shutil.rmtree(configurationDirectory)
	os.makedirs(configurationDirectory)
	common.putIn('0',os.path.normpath(configurationDirectory+'/net-status'),'rewrite')
	
	common.putIn('orphilia_haiku-notify',os.path.normpath(configurationDirectory+'/notify-settings'),'rewrite')
	
	if dropboxPath == "default":	
		dropboxPath = os.path.normpath(home + '/Dropbox')
	else:
		pass
		
	common.putIn(dropboxPath,os.path.normpath(configurationDirectory+'/dropbox-path'),'rewrite')
	if not os.path.exists(dropboxPath):
 		os.makedirs(dropboxPath)

	os.system('orphilia --client \"uid \''+os.path.normpath(configurationDirectory+'/dropbox-id') + '\'\"')
