import os
import subprocess
import shutil
import sys

from setuptools import setup, find_packages

parent_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

INSTALL_REQUIRES = []
if sys.version_info < (2, 6):
    INSTALL_REQUIRES.append('simplejson') # The 'json' module is included with Python 2.6+
    INSTALL_REQUIRES.append('ssl')  # This module is built in to Python 2.6+

extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

    # convert the test code to Python 3
    # because distribute won't do that for us
    # first copy over the tests
    tests_dir = os.path.join(parent_dir, "tests")
    tests3_dir = os.path.join(parent_dir, "3tests")
    if 'test' in sys.argv and os.path.exists(tests_dir):
        shutil.rmtree(tests3_dir, ignore_errors=True)
        shutil.copytree(tests_dir, tests3_dir)
        subprocess.call(["2to3", "-w", "--no-diffs", tests3_dir])
    TEST_SUITE = '3tests'
else:
    TEST_SUITE = 'tests'

#must be called dropbox-client so it overwrites the older dropbox SDK
setup(name='dropbox-python-sdk',
      version='1.5.1',
      description='Official Dropbox REST API Client',
      author='Dropbox, Inc.',
      author_email='support-api@dropbox.com',
      url='http://www.dropbox.com/',
      packages=['dropbox', 'tests'],
      install_requires=INSTALL_REQUIRES,
      package_data={'dropbox': ['trusted-certs.crt'],
                    'tests' : ['server.crt', 'server.key']},
      test_suite=TEST_SUITE,
      tests_require=['mock'],
      **extra
     )
