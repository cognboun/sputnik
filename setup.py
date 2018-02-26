#!/usr/bin/python
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012.11.10
#
# Sputnik Setup
#

from distutils.core import setup
import os

try:
    import setuptools
except ImportError:
    pass

print os.system('! [ -e ./build ] || rm -rf ./build')
print os.system('! [ -e ./sputnik.egg-info ] || rm -rf ./sputnik.egg-info')
print os.system('! [ -e ./dist ] || rm -rf ./dist')

version_text = open('./sputnik/__init__.py', 'r').readlines()
for line in version_text:
    if line.startswith('version'):
        sputnik_version = line.split(' = ')[1].strip()[1:-1]

setup(
    name = "sputnik",
    version = sputnik_version,
    url = 'http://www.msx.com/',
    author = 'error.d',
    author_email = 'error.d@gmail.com',
    description = 'msx Web Framework',
    packages = [
        'sputnik',
        'sputnik/thirdparty',
        'sputnik/thirdparty/new_weibopy',
        'sputnik/thirdparty/qqweibo',
        'sputnik/thirdparty/weibopy',
        'sputnik/thirdparty/tweibo',
        'sputnik/tools/errormonitor',
        'sputnik/tools/loganalyze',
        ],
    scripts = [
        'scripts/sputnik',
        'scripts/scalltrack',
        'server/fastmq_server'
        ],
)
