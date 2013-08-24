# Orphilia build script
#
import os, sys, shutil

build_path = os.getcwd()
parser = 'generic-parser.py'

try:
	sys.argv[1]
except:
	platform=sys.platform
else:
	if sys.argv[1] != "--force":
		platform=sys.argv[1]
	else:
		platform=sys.platform
	
def gentree():
	try:
		if os.path.exists(build_path + "/built"):
			shutil.rmtree(build_path + "/built")
	except:
		print(" [FAILED]")
		print("Error while removing old files. Check if you have read/write permissions to this catalog.")
		sys.exit(1)

	try:
		os.mkdir(build_path + '/built')
		os.mkdir(build_path + '/built/dependencies')
		os.mkdir(build_path + '/built/dropbox')
		os.mkdir(build_path + '/built/orphilia')
		os.mkdir(build_path + '/built/orphiliaclient')
		os.mkdir(build_path + '/built/shared')

		if platform[:5] == "haiku":
			os.mkdir(build_path + '/built/img')

		os.mkdir(build_path + '/built/branding')
		os.mkdir(build_path + '/built/notify')
	except:
		print(" [FAILED]")
		print("Unable to generate directory tree. Check if you have read/write permissions to this catalog.")
		sys.exit(1)
	print(" [OK]")
	
def make_executable(path):
	if sys.platform[:5] == "haiku":
		os.system('chmod +x '+path)
		
	elif sys.platform[:5] != "win32":
		perm = os.stat(path)
		os.chmod(path, perm.st_mode | stat.S_IEXEC)
	
def join_files(fromfile,tofile):
	try:
		second = open(fromfile,"r")
	except:
		print(fromfile + " not found")
		raise
	else:
		f = open(tofile,"a")
		f.write(second.read())
		f.close
		second.close
		
def genorphilia():
	try:
		try:
			join_files(build_path + '/modules/parser/'+ parser,build_path + '/built/orphilia2.py')
		except:
			print(" [FAILED]")
			print("Unable to join files " + build_path + '/modules/parser/'+ parser + " and " + build_path + '/built/orphilia2.py')
			raise
		else:
			try:
				join_files('orphilia.py',build_path + '/built/orphilia2.py')
			except:
				print(" [FAILED]")
				print("Unable to join files orphilia.py and " + build_path + '/built/orphilia2.py')
				raise
			
		if platform != "win32":		
			os.system("tr -d '\r' <"+build_path+"/built/orphilia2.py> " + build_path + "/built/orphilia.py")
		else:
			shutil.copy(build_path+"/built/orphilia2.py",build_path + "/built/orphilia.py")
		
		try:
			os.remove(build_path + '/built/orphilia2.py')
		except:
			print(" [FAILED]")
			print("Unable to remove "+ build_path + "/build/orphilia2.py")
			raise
		
		try:
			make_executable(build_path + '/built/orphilia.py')
		except:
			print("Unable to set executable bit for " + build_path + '/built/orphilia.py')
			
	except:
		print("Unable to generate orphilia.py. Check if you have read/write permissions to this catalog.")
		sys.exit(1)
		
	print(" [OK]")

def copyfiles():
	try:
		#copy Dropbox libraries
		shutil.copy(build_path + '/modules/dropbox/__init__.py',build_path + '/built/dropbox')
		shutil.copy(build_path + '/modules/dropbox/client.py',build_path + '/built/dropbox')
		shutil.copy(build_path + '/modules/dropbox/six.py',build_path + '/built/dropbox')
		shutil.copy(build_path + '/modules/dropbox/util.py',build_path + '/built/dropbox')
		shutil.copy(build_path + '/modules/dropbox/session.py',build_path + '/built/dropbox')
		shutil.copy(build_path + '/modules/dropbox/rest.py',build_path + '/built/dropbox')

		#copy additional modules
		shutil.copy(build_path + '/modules/shared/__init__.py',build_path + '/built/shared')
		shutil.copy(build_path + '/modules/shared/path_rewrite.py',build_path + '/built/shared')
		shutil.copy(build_path + '/modules/shared/date_rewrite.py',build_path + '/built/shared')

		#copy Orphilia modules
		shutil.copy(build_path + '/modules/orphilia/__init__.py',build_path + '/built/orphilia')
		shutil.copy(build_path + '/modules/orphilia/common.py',build_path + '/built/orphilia')
		shutil.copy(build_path + '/modules/orphilia/config.py',build_path + '/built/orphilia')
		shutil.copy(build_path + '/modules/orphilia/installer.py',build_path + '/built/orphilia')
		
		shutil.copy(build_path + '/modules/orphiliaclient/__init__.py',build_path + '/built/orphiliaclient')
		shutil.copy(build_path + '/modules/orphiliaclient/client.py',build_path + '/built/orphiliaclient')
		shutil.copy(build_path + '/modules/orphiliaclient/monitor.py',build_path + '/built/orphiliaclient')
		shutil.copy(build_path + '/modules/orphiliaclient/delta.py',build_path + '/built/orphiliaclient')
		
		#copy dependencies
		shutil.copy(build_path + '/dependencies/ez_setup.py',build_path + '/built/dependencies')
		shutil.copy(build_path + '/dependencies/setup.py',build_path + '/built/dependencies')

		#copy notification related files
		shutil.copy(build_path + '/modules/notify/cli-notify',build_path + '/built/notify')
		shutil.copy(build_path + '/modules/notify/haiku-notify',build_path + '/built/notify')
		shutil.copy(build_path + '/modules/notify/orphilia.png',build_path + '/built/notify')

		#copy branding related files
		shutil.copy(build_path + '/modules/branding/orphilia.png',build_path + '/built/branding')
		shutil.copy(build_path + '/modules/branding/orphilia_haiku.png',build_path + '/built/branding')
		shutil.copy(build_path + '/modules/branding/orphilia_new.png',build_path + '/built/branding')

		#copy cert, readme etc.
		shutil.copy(build_path + '/README',build_path + '/built')
		shutil.copy(build_path + '/modules/dropbox/trusted-certs.crt',build_path + '/built/dropbox')
	except:
		print(" [FAILED]")
		print("Unable to copy files. Check if you have read/write permissions to this catalog.")
		sys.exit(1)
	print(" [OK]")

def buildorphilia():
	print("Generating tree..."),
	gentree()
	print("Generating orphilia.py..."),
	genorphilia()
	print("Copying additional files..."),
	copyfiles()
	
	#platform specific
	if platform[:5] == "haiku":
		print("Copying platform-specific files..."),
		try:
			shutil.copy(build_path + '/modules/haiku-gui/authorize.yab',build_path + '/built')
			shutil.copy(build_path + '/modules/haiku-gui/configuration.yab',build_path + '/built')
			shutil.copy(build_path + '/modules/haiku-gui/install_haiku.sh',build_path + '/built')
			shutil.copy(build_path + '/modules/haiku-gui/yab',build_path + '/built')

			shutil.copy(build_path + '/modules/haiku-gui/img/step.png',build_path + '/built/img')
			
			make_executable(build_path + '/built/yab')
			make_executable(build_path + '/built/install_haiku.sh')
			
		except:
			print(" [FAILED]")
			print("Check if you have read/write permissions to this catalog.")
			sys.exit(1)
		print(" [OK]")
		
	if platform[:5] == "win32":
		print("Copying platform-specific files..."),
		try:
			shutil.copy(build_path + '/modules/windows-workaround/orphilia.bat',build_path + '/built')
			
		except:
			print(" [FAILED]")
			print("Check if you have read/write permissions to this catalog.")
			sys.exit(1)
		print(" [OK]")
		
def warn():
	print(" "+platform+" [WARNING]")
	print("Please bear in mind, that this platform is not supported in this revision")
		
def checkforced():
	try:
		sys.argv[1]
	except:
		print(" "+platform+" [FAILED]")
	else:
		if sys.argv[1] == "--force":
			warn()
			parser = 'haiku-parser.py'
			buildorphilia()
		else:
			try:
				sys.argv[2]
			except:
				print(" "+platform+" [FAILED]")
				print("Argument invalid. Try \"--force\"")
			else:
				if sys.argv[2] == "--force":
					warn()
					parser = 'haiku-parser.py'
					buildorphilia()
				else:
					print(" "+platform+" [FAILED]")
					print("Argument invalid. Try \"--force\"")

print("Parsing build scripts")
print("Identifying platform..."),

if platform[:5] == "haiku":
	print(" Haiku [OK]")
	parser = 'haiku-parser.py'
	buildorphilia()
	
elif platform[:5] == "linux":
	print(" Linux [OK]")
	buildorphilia()

elif platform[:7] == "freebsd":
	print(" FreeBSD [OK]")
	buildorphilia()
	
elif platform[:5] == "win32":
	print(" Windows [OK]")
	buildorphilia()
	
else:
	checkforced()
