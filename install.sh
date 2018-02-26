#! /bin/bash
#
# install.sh
# Copyright (C) 2013 niusmallnan <zhangzhibo521@gmail.com>
#
# Distributed under terms of the MIT license.
#



python setup.py install

rm -rf build
rm -rf dist
rm -rf *.egg-info


