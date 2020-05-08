#!/bin/bash

set -e
set -x

echo "Building..."

docker build -t buzzdb:latest db/

docker build -t buzzserver:latest server/

echo "done"
