rm orphilia
cat build/parser.py >> compiled/orphilia.py
cat orphilia.py >> compiled/orphilia.py
cp db_client.py compiled
cp db_rest.py compiled
cp db_session.py compiled

cat main.py >> orphilia.py
tr -d '\r' <orphilia.py> orphilia
rm orphilia.py
chmod +x orphilia
echo Build scripts parsed.
