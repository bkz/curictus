#!/usr/bin/env bash
sudo svc -u /etc/service/server1
sleep 1
sudo svstat /etc/service/server1

sudo svc -u /etc/service/server2
sleep 1
sudo svstat /etc/service/server2
