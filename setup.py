#!/usr/bin/python
#
# Copyright 2012 msx.com
# by cognboun@gmail.com
# 2012.11.10
#
# Sputnik Setup
#

from distutils.core import setup
import os

try:
    import setuptools
    from setuptools import find_packages
except ImportError:
    pass

print(os.system('! [ -e ./build ] || rm -rf ./build'))
print(os.system('! [ -e ./sputnik.egg-info ] || rm -rf ./sputnik.egg-info'))
print(os.system('! [ -e ./dist ] || rm -rf ./dist'))

version_text = open('./sputnik/__init__.py', 'r').readlines()
for line in version_text:
    if line.startswith('version'):
        sputnik_version = line.split(' = ')[1].strip()[1:-1]

with open("README.md", "r") as f:
  long_description = f.read()
        
setup(
    name = "sputnik-web",
    version = sputnik_version,
    description='sputnik is web framework',
    long_description=long_description,
    author='cognboun',
    author_email='cognboun@gmail.com',
    url='https://github.com/cognboun/sputnik',
    project_urls={
        "Source": "https://github.com/cognboun/sputnik",
    },
    install_requires=[
        'arrow>=1.1.0',
        'requests>=2.20.1',
        'pymongo==2.6.1',
        'pyzmq==14.4.1',
        'redis==2.10.3',
        'requests==2.8.1',
        'thrift==0.9.1',
        'tornado==2.1.1',
		"event_time_format>=1.0.2"
    ],
    license='BSD License',
    scripts = [
        'scripts/sputnik',
        'scripts/scalltrack',
        'server/fastmq_server'
        ],
    packages=find_packages(),
    platforms=["all"],
    classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Natural Language :: Chinese (Simplified)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Topic :: Software Development :: Libraries'
      ],

)
