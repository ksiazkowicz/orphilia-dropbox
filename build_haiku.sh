##remove any previously built files
rm -r built_files

##generate directory tree
##
mkdir built_files
mkdir built_files/dependencies
mkdir built_files/img
mkdir built_files/branding
mkdir built_files/notify

##generate orphilia using parser.py, header.py, dropbox API files and main.py
##
cat build/haiku-parser.py >> built_files/orphilia.py
cat header.py >> built_files/orphilia.py
cat api/client.py >> built_files/orphilia.py
cat api/rest.py >> built_files/orphilia.py
cat api/session.py >> built_files/orphilia.py
cat main.py >> built_files/orphilia.py
tr -d '\r' <built_files/orphilia.py> built_files/orphilia
rm built_files/orphilia.py
chmod +x built_files/orphilia


##copy all other files
cp haiku-gui/install_haiku.sh built_files/install_haiku.sh
cp README built_files
cp trusted-certs.crt built_files
cp yab built_files
cp haiku-gui/configuration.yab built_files
cp haiku-gui/authorize.yab built_files
cp haiku-gui/img/* built_files/img
cp branding/* built_files/branding
cp notify/* built_files/notify
cp dependencies/* built_files/dependencies

echo Build scripts parsed.
