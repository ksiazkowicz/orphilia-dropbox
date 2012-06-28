##remove any previously built files
rm -r built

##generate directory tree
##
mkdir built
mkdir built/dependencies
mkdir built/img
mkdir built/branding
mkdir built/notify

##generate orphilia using parser.py, header.py, dropbox API files and main.py
##
cat build/haiku-parser.py >> built/orphilia.py
cat orphilia.py >> built/orphilia.py
cp db_client.py built
cp db_rest.py built
cp db_session.py built
cp date_rewrite.py built
cp path_rewrite.py built
cp orphilia_shared.py built
tr -d '\r' <built/orphilia.py> built/orphilia
rm built/orphilia.py
chmod +x built/orphilia


##copy all other files
cp haiku-gui/install_haiku.sh built/install_haiku.sh
cp README built
cp trusted-certs.crt built
cp yab built
cp haiku-gui/configuration.yab built
cp haiku-gui/authorize.yab built
cp haiku-gui/img/* built/img
cp branding/* built/branding
cp notify/* built/notify
cp dependencies/* built/dependencies

echo Build scripts parsed.
