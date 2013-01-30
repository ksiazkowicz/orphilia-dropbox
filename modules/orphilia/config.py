import sys
import os
import shutil

home = os.path.expanduser('~')

# set configurationdir path dependent from platform
if sys.platform[:5] == 'haiku':
	configurationdir = os.path.normpath(home + '/config/settings/Orphilia/')
elif sys.platform[:3] == 'win':
	configurationdir = os.path.normpath(home + '/AppData/Roaming/Orphilia/')
else:
	configurationdir = os.path.normpath(home + '/.orphilia/')

def putin(string,filename,method):
	if method == "append":
		putinfile = open(filename,"a")
	else:
		putinfile = open(filename,"w")
	putinfile.write(string)
	putinfile.close

def config():
	if os.path.isdir(configurationdir):
		shutil.rmtree(configurationdir)
	os.makedirs(configurationdir)
	putin('0',os.path.normpath(configurationdir+'/net-status'),'rewrite')
	print("Welcome to Orphilia, an open-source crossplatform Dropbox client.\nIn few steps, you will configure your Dropbox account to be used with Orphilia.")
	
	if sys.platform[:5] == "haiku":
		putin('orphilia_haiku-notify',os.path.normpath(configurationdir+'/notify-settings'),'rewrite')

	else:
		notifier = raw_input("Enter notify method: ")
		putin(notifier,os.path.normpath(configurationdir+'/notify-settings'),'rewrite')

	droppath = raw_input("Dropbox folder location (optional):")
	
	if droppath == "":	
		droppath = os.path.normpath(home + '/Dropbox')
	else:
		pass
		
	putin(droppath,os.path.normpath(configurationdir+'/dropbox-path'),'rewrite')
	if not os.path.exists(droppath):
 		os.makedirs(droppath)

	print("Please wait. Orphilia is making configuration files.")
	os.system('orphilia --client--silent \"uid \''+os.path.normpath(configurationdir+'/dropbox-id') + '\'\"')

	print("Configuration files has been created.")

def config_gui():
	if os.path.isdir(configurationdir):
		shutil.rmtree(configurationdir)
	os.makedirs(configurationdir)
	putin('0',os.path.normpath(configurationdir+'/net-status'),'rewrite')
	
	putin('orphilia_haiku-notify',os.path.normpath(configurationdir+'/notify-settings'),'rewrite')

	droppath = sys.argv[2]
	
	if droppath == "default":	
		droppath = os.path.normpath(home + '/Dropbox')
	else:
		pass
		
	putin(droppath,os.path.normpath(configurationdir+'/dropbox-path'),'rewrite')
	if not os.path.exists(droppath):
 		os.makedirs(droppath)

	os.system('orphilia --client--silent \"uid \''+os.path.normpath(configurationdir+'/dropbox-id') + '\'\"')
