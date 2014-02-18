import ez_setup, sys
ez_setup.use_setuptools()
from setuptools import setup, find_packages

INSTALL_REQUIRES = []
INSTALL_REQUIRES.append('urllib3')  # This is a 3rd party connections lib for 2.6+
assert sys.version_info >= (2, 6), "We only support Python 2.6+"
INSTALL_REQUIRES.append('oauth')
INSTALL_REQUIRES.append('simplejson')
INSTALL_REQUIRES.append('watchdog')

setup(name='orphilia-dependencies',
      version='0.2',
      description='Modules required to run Orphilia',
      author='Maciej Janiszewski',
      author_email='pisarzk@gmail.com',
	  install_requires=INSTALL_REQUIRES
     )
