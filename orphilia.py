import sys

####### Orphilia-specific modules
import orphilia

#generate sys.argv dictionary
if len(sys.argv) > 1:
	parameters = sys.argv[2:]
	wtd = sys.argv[1]
else:
	wtd = "brick"

if wtd == "--client":
    orphilia.client.client_verbose(parameters)
	
if wtd == "--client-old":
    orphilia.client.client_new(parameters)

elif wtd == "--client--silent":
    orphilia.client.orphilia_new(parameters)

elif wtd == "--install":
    orphilia.installer.install()

elif wtd == "--uninstall":
    orphilia.installer.uninstall()

elif wtd == "--help":
	print("""Orphilia
Maciej Janiszewski, 2010-2013
made with Dropbox SDK from https://www.dropbox.com/developers/reference/sdk

Syntax: orphilia [OPTION] [PARAMETERS]
	
 --help          - displays this text
 --monitor       - monitors Dropbox folder activity
 --configuration - runs configuration wizard
 --public        - generates public links
 --install       - installs Orphilia
 --uninstall     - uninstalls Orphilia
 --client        - runs Orphilia API Client
   syntax: orphilia --client [parameter1] [parameter2] [parameter3]
    get   [from path] [to path] - downloads file
    put   [from path] [to path] - uploads file
    mv    [from path] [to path] - moves and renames file
    rm    [path]                - removes a file
    ls    [path]      [to file] - creates a list of files in directory
    mkdir [path]                - creates a directory
    uid   [path]                - gets current accounts Dropbox UID""")

elif wtd == "--configuration":
    orphilia.config.config()

elif wtd == "--configuration-haiku":
    orphilia.config.config_gui(parameters)

elif wtd == "--monitor":
    orphilia.monitor.monitor()

elif wtd == "--public":
    orphilia.client.public(parameters)

else:
     print("Invalid syntax. Type orphilia --help for more informations")

