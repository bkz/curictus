#!/usr/bin/env bash
cd dist
svn update media
svn update modules
rm bootstrap.py
svn export https://svn.curictus.se/svn/curictus/trunk/Curegame/bootstrap.py
cd ~


