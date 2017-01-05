#!/usr/bin/env bash

SVN=https://svn.curictus.se/svn/curictus/

if [ -d ~/dist/amender ]
then
	echo Updating to latest version in SVN.
	cd ~/dist/amender && svn update
else
	echo Checkout latest version from SVN.
	mkdir -p ~/dist && cd ~/dist
	svn co $SVN/trunk/tools/amender
fi

