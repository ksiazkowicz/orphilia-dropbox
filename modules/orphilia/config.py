import sys, os, shutil, orphilia

home = os.path.expanduser('~')

# set configurationDirectory path dependent from platform
configurationDirectory = orphilia.client.getConfigurationDirectory()

def putIn(string,filename,method):
	if method == "append":
		putInFile = open(filename,"a")
	else:
		putInFile = open(filename,"w")
	putInFile.write(string)
	putInFile.close

def config():
	if os.path.isdir(configurationDirectory):
		shutil.rmtree(configurationDirectory)
	os.makedirs(configurationDirectory)
	putIn('0',os.path.normpath(configurationDirectory+'/net-status'),'rewrite')
	print("Welcome to Orphilia, an open-source crossplatform Dropbox client.\nIn few steps, you will configure your Dropbox account to be used with Orphilia.")
	
	if sys.platform[:5] == "haiku":
		putIn('orphilia_haiku-notify',os.path.normpath(configurationDirectory+'/notify-settings'),'rewrite')

	else:
		notifier = raw_input("Enter notify method: ")
		putIn(notifier,os.path.normpath(configurationDirectory+'/notify-settings'),'rewrite')

	dropboxPath = raw_input("Dropbox folder location (optional):")
	
	if dropboxPath == "":	
		dropboxPath = os.path.normpath(home + '/Dropbox')
	else:
		pass
		
	putIn(dropboxPath,os.path.normpath(configurationDirectory+'/dropbox-path'),'rewrite')
	if not os.path.exists(dropboxPath):
 		os.makedirs(dropboxPath)

	print("Please wait. Orphilia is making configuration files.")
	os.system('orphilia --client--silent \"uid \''+os.path.normpath(configurationDirectory+'/dropbox-id') + '\'\"')

	print("Configuration files has been created.")

def config_gui():
	if os.path.isdir(configurationDirectory):
		shutil.rmtree(configurationDirectory)
	os.makedirs(configurationDirectory)
	putIn('0',os.path.normpath(configurationDirectory+'/net-status'),'rewrite')
	
	putIn('orphilia_haiku-notify',os.path.normpath(configurationDirectory+'/notify-settings'),'rewrite')

	dropboxPath = sys.argv[2]
	
	if dropboxPath == "default":	
		dropboxPath = os.path.normpath(home + '/Dropbox')
	else:
		pass
		
	putIn(dropboxPath,os.path.normpath(configurationDirectory+'/dropbox-path'),'rewrite')
	if not os.path.exists(dropboxPath):
 		os.makedirs(dropboxPath)

	os.system('orphilia --client \"uid \''+os.path.normpath(configurationDirectory+'/dropbox-id') + '\'\"')
