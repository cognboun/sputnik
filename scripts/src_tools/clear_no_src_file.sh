#!/bin/sh

rm -rf ../../build
rm -rf ../../dist
rm -rf ../../sputnik.egg-info

cd ../../
find ./ | grep -E '\.pyc$' | xargs rm -rf
rm -rf log/*.*
