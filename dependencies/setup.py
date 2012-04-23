import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(name='orphilia-dependencies',
      version='0.1',
      description='Modules required to run Orphilia',
      author='Maciej Janiszewski',
      author_email='pisarzk@gmail.com',
      install_requires = ['oauth', 'simplejson', 'watchdog'],
     )
