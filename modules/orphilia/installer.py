import sys
import os
import shutil

def install():
	print('Orphilia Installer')
	print('---')
	# check if command is supported on this platform
	if sys.platform[:3] == 'win':
		print('This function is not available on this platform')
		sys.exit(1)

	# define generic installdir and bindir
	installdir = '/usr/share/orphilia'
	bindir = '/usr/share/bin'

	# use Haiku-specific installdir and bindir	
	if sys.platform[:5] == 'haiku':
		installdir = '/boot/apps/orphilia'
		bindir = '/boot/common/bin'

	#generic instructions
	os.chmod('./orphilia.py',755) # make orphilia.py executable
	try:
	# generate directory tree
		os.mkdir(installdir)
		os.mkdir(installdir + '/dropbox')
		os.mkdir(installdir + '/orphilia')
		os.mkdir(installdir + '/shared')
	except:
		print('Unable to make install directory tree')
		sys.exit(1)
	
	try:
	# copy all the files
		shutil.copy('./orphilia.py',installdir)
	
		shutil.copy('./dropbox/__init__.pyc',installdir + '/dropbox')
		shutil.copy('./dropbox/six.pyc',installdir + '/dropbox')
		shutil.copy('./dropbox/client.pyc',installdir + '/dropbox')
		shutil.copy('./dropbox/session.pyc',installdir + '/dropbox')
		shutil.copy('./dropbox/rest.pyc',installdir + '/dropbox')

		#copy additional modules
		shutil.copy('./shared/__init__.pyc',installdir + '/shared')
		shutil.copy('./shared/path_rewrite.pyc',installdir + '/shared')
		shutil.copy('./shared/date_rewrite.pyc',installdir + '/shared')

		#copy Orphilia modules
		shutil.copy('./orphilia/__init__.pyc',installdir + '/orphilia')
		shutil.copy('./orphilia/client.pyc',installdir + '/orphilia')
		shutil.copy('./orphilia/config.pyc',installdir + '/orphilia')
		shutil.copy('./orphilia/installer.pyc',installdir + '/orphilia')
		shutil.copy('./orphilia/monitor.pyc',installdir + '/orphilia')

		#copy notify scripts
		shutil.copy('./notify/cli-notify',installdir)
		os.chmod(installdir + '/cli-notify',755)
		
		#copy platform-specific notify scripts
		if sys.platform[:5] == "haiku":
			shutil.copy('./notify/haiku-notify',installdir)
			os.chmod(installdir + '/haiku-notify',755)

		#copy branding related files
		shutil.copy('./branding/orphilia.png',installdir + '/branding')
	
		if sys.platform[:5] == "haiku":
			shutil.copy('./branding/orphilia_haiku.png',installdir)
		else:
			shutil.copy('./branding/orphilia.png','/usr/share/pixmaps')

		shutil.copy('./dropbox/trusted-certs.crt',installdir + '/dropbox')

		#copy platform-specific files (gui)	
		if sys.platform[:5] == "haiku":
			shutil.copy('./authorize.yab',installdir + '/authorize.yab')
			shutil.copy('./yab', installdir)
			os.chmod(installdir + '/yab',755)
			os.chmod(installdir + '/authorize.yab',755)
	
		#make symlinks
		os.symlink(installdir + '/orphilia.py',bindir + '/orphilia')
		os.symlink(installdir + '/cli-notify',bindir + '/orphilia_cli-notify')
		os.symlink(installdir + '/authorize.yab',bindir +'/orphilia_haiku-authorize')
		
		if sys.platform[:5] == 'haiku':
			os.system('alert --info \"Installation completed.\"')
			os.system('ln -s ' + installdir + '/haiku-notify ' + bindir + '/orphilia_haiku-notify')
			
		print('Done. Now run orphilia --configuration as a regular user')

	except:
		print('Installation failed.')

def uninstall():
	print('Orphilia Installer')
	print('---')
	# check if command is supported on this platform
	if sys.platform[:3] == 'win':
		print('This function is not available on this platform')
		sys.exit(1)
    
	installdir = '/usr/share/orphilia'
	bindir = '/usr/share/bin'
	
	if sys.platform[:5] == 'haiku':
		installdir = '/boot/apps/orphilia'
		bindir = '/boot/common/bin'
		
	os.remove(installdir)
	os.remove(bindir + '/orphilia')
	os.remove(bindir + '/orphilia_cli-notify')
	
	if sys.platform[:5] == "haiku":
		os.remove(bindir + '/orphilia_haiku-notify')
		os.remove(bindir + '/orphilia_haiku-authorize')
		os.system('alert --info \"Uninstallation completed.\"')
	else:
		os.remove('/usr/share/pixmaps/orphilia.png')
	
	print('Done.')
