#!/bin/sh

basedir=`dirname "$0"`
cd $basedir

cd dependencies
python setup.py install
cd ..
yab configuration.yab
