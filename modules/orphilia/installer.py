import sys, os, shutil

def make_executable(path):
	if sys.platform[:5] == "haiku":
		os.system('chmod +x '+path)
		
	elif sys.platform[:5] != "win32":
		perm = os.stat(path)
		os.chmod(path, perm.st_mode | stat.S_IEXEC)
	
def install():
	print('Orphilia Installer')
	print('---')
	
	# define generic installdir and bindir
	installdir = '/usr/share/orphilia'
	bindir = '/usr/share/bin'
	
	# check if command is supported on this platform
	if sys.platform[:5] == 'win32':
		print('This function is not available on this platform')
		sys.exit(1)

	# use Haiku-specific installdir and bindir	
	if sys.platform[:5] == 'haiku':
		installdir = '/boot/apps/orphilia'
		bindir = '/boot/common/bin'
		
	print(installdir)
	print(bindir)

	#generic instructions
	make_executable('./orphilia.py')
	try:
	# generate directory tree
		os.mkdir(installdir)
		os.mkdir(installdir + '/dropbox')
		os.mkdir(installdir + '/orphilia')
		os.mkdir(installdir + '/orphiliaclient')
		os.mkdir(installdir + '/shared')
	except:
		print('Unable to make install directory tree')
		sys.exit(1)
	
	try:
	# copy all the files
		shutil.copy('./orphilia.py',installdir)
	
		shutil.copy('./dropbox/__init__.py',installdir + '/dropbox')
		shutil.copy('./dropbox/six.py',installdir + '/dropbox')
		shutil.copy('./dropbox/client.py',installdir + '/dropbox')
		shutil.copy('./dropbox/session.py',installdir + '/dropbox')
		shutil.copy('./dropbox/rest.py',installdir + '/dropbox')

		#copy additional modules
		shutil.copy('./shared/__init__.py',installdir + '/shared')
		shutil.copy('./shared/path_rewrite.py',installdir + '/shared')
		shutil.copy('./shared/date_rewrite.py',installdir + '/shared')

		#copy Orphilia modules
		shutil.copy('./orphilia/__init__.py',installdir + '/orphilia')
		shutil.copy('./orphilia/common.py',installdir + '/orphilia')
		shutil.copy('./orphilia/config.py',installdir + '/orphilia')
		shutil.copy('./orphilia/installer.py',installdir + '/orphilia')
		
		shutil.copy('./orphiliaclient/__init__.py', installdir + '/orphiliaclient')
		shutil.copy('./orphiliaclient/client.py', installdir + '/orphiliaclient')
		shutil.copy('./orphiliaclient/monitor.py', installdir + '/orphiliaclient')

		#copy notify scripts
		shutil.copy('./notify/cli-notify',installdir)
		make_executable(installdir + '/cli-notify')
		
		#copy platform-specific notify scripts
		if sys.platform[:5] == "haiku":
			shutil.copy('./notify/haiku-notify',installdir)
			make_executable(installdir + '/haiku-notify')

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
			make_executable(installdir + '/yab')
			make_executable(installdir + '/authorize.yab')
	
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
		
	shutil.rmtree(installdir)
	os.remove(bindir + '/orphilia')
	os.remove(bindir + '/orphilia_cli-notify')
	
	if sys.platform[:5] == "haiku":
		os.remove(bindir + '/orphilia_haiku-notify')
		os.remove(bindir + '/orphilia_haiku-authorize')
		os.system('alert --info \"Uninstallation completed.\"')
	else:
		os.remove('/usr/share/pixmaps/orphilia.png')
	
	print('Done.')
