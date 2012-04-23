@echo off
del orphilia.py
type parser.py >> orphilia.py
type header.py >> orphilia.py
type api\client.py >> orphilia.py
type api\rest.py >> orphilia.py
type api\session.py >> orphilia.py
type main.py >> orphilia.py
echo Build scripts parsed.