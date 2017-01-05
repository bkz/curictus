#!/usr/bin/env bash
sudo ./stop.sh

rm -rf server1/bootstrap.py server1/media server1/modules 
cp -R dist/bootstrap.py dist/media dist/modules server1/

rm -rf server2/bootstrap.py server2/media server2/modules 
cp -R dist/bootstrap.py dist/media dist/modules server2/

sudo ./start.sh
