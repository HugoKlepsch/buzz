#!/bin/bash

set -e

./stop.sh

echo "Pruning old docker network..."
docker network prune -f

echo "Creating docker network..."
docker network create buzz

echo "Starting db container..."
docker run -d -p 5432:5432 --net buzz --name buzzdb buzzdb:latest

echo "Starting server container..."
docker run --env-file server/env.env -d -p 14532:80 --net buzz --name buzzserver buzzserver:latest
set +x

echo "To see logs of db, type 'docker logs -f buzzdb'"
echo "To see logs of server, type 'docker logs -f buzzserver'"
echo "View website at http://localhost:14532"

