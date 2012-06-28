import sys

####### Dropbox SDK
import db_rest
import db_session
import db_client

####### Orphilia-specific modules
import path_rewrite
import date_rewrite
import orphilia_shared

if len(sys.argv) > 1:
    wtd = sys.argv[1]
else:
    wtd = "brick"

if wtd == "--client":
    orphilia_shared.kanapki()

elif wtd == "--client--silent":
    orphilia_shared.client()

elif wtd == "--install":
    orphilia_shared.install()

elif wtd == "--uninstall":
    orphilia_shared.uninstall()

elif wtd == "--help":
    orphilia_shared.help()

elif wtd == "--configuration":
    orphilia_shared.config()

elif wtd == "--configuration-haiku":
    orphilia_shared.config_gui()

elif wtd == "--monitor":
    orphilia_shared.monitor()

elif wtd == "--public":
    orphilia_shared.public()

else:
     print("Invalid syntax. Type orphilia --help for more informations")

