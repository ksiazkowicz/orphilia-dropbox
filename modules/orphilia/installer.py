import sys
import os
import shutil

def install():
	print "Orphilia Installer"
	print "---"

	installdir = "/usr/share/orphilia"
	bindir = "/usr/share/bin"
	
	if sys.platform[:5] == "haiku":
		installdir = "/boot/apps/orphilia"
		bindir = "/boot/common/bin"

	#generic instructions
	os.system("chmod +x ./orphilia.py")
	try:
		os.mkdir(installdir)
		os.mkdir(installdir + '/dropbox')
		os.mkdir(installdir + '/orphilia')
		os.mkdir(installdir + '/shared')
	except:
		print('Unable to make install directory tree')
		sys.exit(1)
	
	try:
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
		os.system('chmod +x ' + installdir + '/cli-notify')
		
		#copy platform-specific notify scripts
		if sys.platform[:5] == "haiku":
			shutil.copy('./notify/haiku-notify',installdir)
			os.system('chmod +x ' + installdir + '/haiku-notify')

		#copy branding related files
		shutil.copy('./branding/orphilia.png',installdir + '/branding')
	
		if sys.platform[:5] == "haiku":
			shutil.copy('./branding/orphilia_haiku.png',installdir)
		else:
			shutil.copy('./branding/orphilia.png','/usr/share/pixmaps')

		shutil.copy('./trusted-certs.crt',installdir)

		#copy platform-specific files (gui)	
		if sys.platform[:5] == "haiku":
			shutil.copy('./authorize.yab',installdir + '/authorize.yab')
			shutil.copy('./yab', installdir)
			os.system('chmod +x ' + installdir + '/yab')
	
		#make symlinks
		os.system('ln -s ' + installdir + '/orphilia.py ' + bindir + '/orphilia')
		os.system('ln -s ' + installdir + '/cli-notify ' + bindir + '/orphilia_cli-notify')
		os.system('ln -s ' + installdir + '/authorize.yab ' + bindir + '/orphilia_haiku-authorize')
		
		if sys.platform[:5] == "haiku":
			os.system('alert --info \"Installation completed.\"')
			os.system('ln -s ' + installdir + '/haiku-notify ' + bindir + '/orphilia_haiku-notify')
			
		print "Done. Now run orphilia --configuration as a regular user"

	except:
		print('Installation failed.')

def uninstall():
	print "Orphilia Installer"
	print "---"
    
	installdir = "/usr/share/orphilia"
	bindir = "/usr/share/bin"
	
	if sys.platform[:5] == "haiku":
		installdir = "/boot/apps/orphilia"
		bindir = "/boot/common/bin"
		
	os.system("rm -r " + installdir)
	os.system("rm " + bindir + "/orphilia")
	os.system("rm " + bindir + "/orphilia_cli-notify")
	
	if sys.platform[:5] == "haiku":
		os.system("rm " + bindir + "/orphilia_haiku-notify")
		os.system("rm " + bindir + "/orphilia_haiku-authorize")
		os.system('alert --info \"Uninstallation completed.\"')
	else:
		os.system("rm /usr/share/pixmaps/orphilia.png")
	
	print "Done."
