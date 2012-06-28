rm orphilia
cat build/parser.py >> built/orphilia.py
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
echo Build scripts parsed.
