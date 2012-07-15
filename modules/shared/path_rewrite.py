import os
import urllib
import urlparse

def parts(path): 
    components = []  
    while True: 
        (path,tail) = os.path.split(path) 
        if tail == "": 
            components.reverse() 
            return components 
        components.append(tail) 

def url_fix(s, charset='utf-8'): 
    if isinstance(s, unicode): 
        s = s.encode(charset, 'ignore') 
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s) 
    path = urllib.quote(path, '/%') 
    qs = urllib.quote_plus(qs, ':&=') 
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor)) 

def rewritepath(os,path): 

    components = parts(path) 
    newpath = ""

    if os == 'nt':
       for item in components:
           newpath = newpath + "\\" + item

    elif os == 'posix':
         for item in components:
             newpath = newpath + "/" + item

    elif os == 'url':
         for item in components:
             newpath = newpath + "/" + item
         newpath = url_fix(newpath)

    newpath = newpath[1:]
    return newpath
