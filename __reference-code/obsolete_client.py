def orphilia_client(parameters):
	statusf = open(os.path.normpath(configurationdir+'/net-status'), 'r')
	status = statusf.read()
	statusf.close()
	if status == "1":
		exit()

	def command(login_required=True):
		def decorate(f):
			def wrapper(self, args):
				if login_required and not self.sess.is_linked():
					self.stdout.write("Please 'login' to execute this command\n")
					return
	
				try:
					return f(self, *args)
				except TypeError as e:
					self.stdout.write(str(e) + '\n')
				except rest.ErrorResponse as e:
					msg = e.user_error_msg or str(e)
					self.stdout.write('Error: %s\n' % msg)
					msg2 = msg[:5]
					if msg2 == "[401]":
						print(" > Token problem. Unlinking..."),
						self.sess.unlink()
						print(" OK")
						self.sess.link()
						print(" > Repeating command...")
						term = DropboxTerm(APP_KEY, APP_SECRET)
						term.onecmd(parameters[1])
	
			wrapper.__doc__ = f.__doc__
			return wrapper
		return decorate

	class DropboxTerm(cmd.Cmd):
		def __init__(self, app_key, app_secret):
			cmd.Cmd.__init__(self)
			self.sess = StoredSession(app_key, app_secret, access_type=ACCESS_TYPE)
			self.api_client = client.DropboxClient(self.sess)
	
			self.sess.load_creds()

		@command()
		def do_sync_everything(self, path):
			term = DropboxTerm(APP_KEY, APP_SECRET)
			resp = self.api_client.metadata(path)
			rand1 = random.random()
			dirlist = os.listdir(droppath + "/" + path)
			to_file = os.path.normpath(configurationdir + "_tmpscript" + str(rand1) + ".tmp")
			file = open(to_file,"w")
			file.write('orphilia --client--silent \"sync_folder \\"' + path + "/" + '\\"\"' + '\n')

			for fname in dirlist:
					if os.path.isdir(droppath + "/" + path + fname):
						file.write('cd \"' + fname + '\"'+ '\n')
						file.write('orphilia --client--silent \"sync_everything \\"' + path + "/" + fname + '\\"\"' + '\n')
						file.write('cd ..'+ '\n')
			file.close()
			os.system("chmod +x " + to_file)
			os.system("sh " + to_file)
			os.system("rm " + to_file)
			print(" > Command '" + parameters[1] + "' executed")

		@command()
		def do_sync_folder(self, path):
			term = DropboxTerm(APP_KEY, APP_SECRET)
			""""""
			resp = self.api_client.metadata(path)
			dirlist = os.listdir(droppath + "/" + path)
			rand1 = random.random()

			if 'contents' in resp:
				for f in resp['contents']:
					name = os.path.basename(f['path'])
					encoding = locale.getdefaultlocale()[1]
					if ('%s' % name).encode(encoding) not in dirlist:
						print ('%s' % name).encode(encoding) + " not found."
						if not os.path.isfile(('%s' % name).encode(encoding)):
							dir = f['is_dir']
							if not dir:
								term.onecmd('get \"' + path + "/" + ('%s' % name).encode(encoding) + '\" \"' +  droppath + "/" + path +  ('%s' % name).encode(encoding) + '\"')
							if dir:
								os.system('mkdir \"' + droppath + "/" + path +  ('%s' % name).encode(encoding) + '\"')
					else:
						name = os.path.basename(f['path'])
						encoding = locale.getdefaultlocale()[1]
						print ('%s' % name).encode(encoding) + " found. Checking..."

						modified = f['modified']
						date1 = modified[5:]
					if os.path.isfile(('%s' % name).encode(encoding)):
						t = time.ctime(os.path.getmtime(('%s' % name).encode(encoding)))
						date2 = t[4:]

						hour = str(int(hour) +1)

						timestamp1_rnd = date_rewrite.generate_timestampd(date1)
						print(date1 + " converted to " + timestamp1_rnd)
						timestamp2_rnd = date_rewrite.generate_timestamp(date2)
						print(date2 + " converted to " + timestamp2_rnd)
						
						dir = f['is_dir']

						if timestamp1_rnd < timestamp2_rnd:
							if not dir:
								print(" - Dropbox version of file \"" + ('%s' % name).encode(encoding) + "\" is older. Updating...")
								term.onecmd('rm \"' +  path + "/" + ('%s' % name).encode(encoding) + '\"')
								term.onecmd('sync \"' + ('%s' % name).encode(encoding) + '\" \"' +  path + "/" + ('%s' % name).encode(encoding) + '\"')
							else:
								print + " x " + name + " is directory. Skipping."

					elif timestamp1_rnd > timestamp2_rnd:
						term.onecmd('get \"' + path + "/" + ('%s' % name).encode(encoding) + '\" \"' +  ('%s' % name).encode(encoding) + '\"')
						print(" - Dropbox verion of file \"" + ('%s' % name).encode(encoding) + "\" is newer. Updating.")

					else:
							print(" x File \"" + ('%s' % name).encode(encoding) + "\" is identical. Skipping.")

				print(" > Command '" + parameters[1] + "' executed")
	
		# the following are for command line magic and aren't Dropbox-related
		def emptyline(self):
			pass

		def do_EOF(self, line):
			self.stdout.write('\n')
			return True

		def parseline(self, line):
			parts = shlex.split(line)
			if len(parts) == 0:
				return None, None, line
			else:
				return parts[0], parts[1:], line


	class StoredSession(session.DropboxSession):
		TOKEN_FILE = os.path.normpath(configurationdir + "/token_store.txt")

		def load_creds(self):
			print(" > Loading access token..."),
			try:
				stored_creds = open(self.TOKEN_FILE).read()
				self.set_token(*stored_creds.split('|'))
				print(" OK")
			except IOError:
				print(" FAILED")
				print(" x Access token not found. Beggining new session.")
				self.link()

		def write_creds(self, token):
			f = open(self.TOKEN_FILE, 'w')
			f.write("|".join([token.key, token.secret]))
			f.close()

		def delete_creds(self):
			os.unlink(self.TOKEN_FILE)
	
		def link(self):
			print(" > Authorizing...")
			request_token = self.obtain_request_token()
			url = self.build_authorize_url(request_token)
			if sys.platform[:5] == "haiku":
					putin(url,os.path.normpath(configurationdir+'/authorize-url'),'rewrite')
					drmchujnia = os.system("orphilia_haiku-authorize")
					os.system('rm ' + os.path.normpath(configurationdir+'/authorize-url'))
			else:
					print("url:", url),
					raw_input()

			self.obtain_access_token(request_token)
			self.write_creds(self.token)

			save_state({
				'access_token': (request_token.key, request_token.secret),
				'tree': {}
			})

		def unlink(self):
			self.delete_creds()
			session.DropboxSession.unlink(self)

	if APP_KEY == '' or APP_SECRET == '':
		exit('You need to set your APP_KEY and APP_SECRET!')
	term = DropboxTerm(APP_KEY, APP_SECRET)
	term.onecmd(parameters)
