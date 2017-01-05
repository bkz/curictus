#!/usr/bin/env bash

SVN=https://svn.curictus.se/svn/curictus/trunk/prerequisites/python
LIBS="simplejson-2.1.1.tar.gz tornado-1.0.tar.gz SQLAlchemy-0.6.0.tar.gz"

# Setup and activate Python server sandbox.
cd ~ && virtualenv --no-site-packages server && source ~/server/bin/activate

# Update to latest version
./update.sh && cp -R ~/dist/amender ~/server 

# Fetch and install Python thirdparty libraries in sandbox.
mkdir -p ~/thirdparty
for filename in $LIBS
do
	svn export $SVN/$filename ~/thirdparty/$filename
	cd ~/thirdparty && tar -xf $filename
	cd ~/thirdparty/${filename%.tar.gz} && python setup.py install	
done
