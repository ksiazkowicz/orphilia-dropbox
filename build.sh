rm orphilia
cat build/parser.py >> orphilia.py
cat header.py >> orphilia.py
cat api/client.py >> orphilia.py
cat api/rest.py >> orphilia.py
cat api/session.py >> orphilia.py
cat main.py >> orphilia.py
tr -d '\r' <orphilia.py> orphilia
rm orphilia.py
chmod +x orphilia
echo Build scripts parsed.
