#!/usr/bin/env bash

cp ~/config.cfg ~/server/amender/
source ~/server/bin/activate
cd ~/server/amender && python main.py

