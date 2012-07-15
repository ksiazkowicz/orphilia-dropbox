import sys

####### Orphilia-specific modules
import orphilia

if len(sys.argv) > 1:
    wtd = sys.argv[1]
else:
    wtd = "brick"

if wtd == "--client":
    orphilia.client.kanapki()

elif wtd == "--client--silent":
    orphilia.client.client()

elif wtd == "--install":
    orphilia.installer.install()

elif wtd == "--uninstall":
    orphilia.installer.uninstall()

elif wtd == "--help":
	print("\n")
	print("Syntax: orphilia [OPTION] [PARAMETERS]")
	print("")
	print("  --help          - displays this text")
	print("  --monitor       - monitors Dropbox folder activity")
	print("  --configuration - runs configuration wizard")
	print("  --public        - generates public links")
	print("  --install       - installs Orphilia")
	print("  --uninstall     - uninstalls Orphilia")
	print("  --client        - runs Orphilia API Client")
	print('     syntax: orphilia --client "\\"[parameter1]\\" \\"[parameter2]\\" \\"[parameter3]\\""')
	print("       get    - downloads file from path specified in parameter2 and saves them to \npath specified in parameter3")
	print("       put    - uploads file from path specified in parameter2 to path specified in \nparameter3")
	print("       mv     - moves file from path specified in parameter2 to path specified in \nparameter3")
	print("       cp     - copies file from path specified in parameter2 to path specified in \nparameter3")
	print("       rm     - removes a file (name specified in parameter2)")
	print("       ls     - creates a list of files in directory specified in parameter2 and \nsaves it to file specified in parameter3")
	print("       mkdir  - creates a directory (name specified in parameter2)")
	print("       uid    - updates Orphilia configuration with current accounts Dropbox UID")

elif wtd == "--configuration":
    orphilia.config.config()

elif wtd == "--configuration-haiku":
    orphilia.config.config_gui()

elif wtd == "--monitor":
    orphilia.monitor.monitor()

elif wtd == "--public":
    orphilia.client.public()

else:
     print("Invalid syntax. Type orphilia --help for more informations")

