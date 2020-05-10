#!/bin/bash

set -e

echo "Stopping containers..."
docker kill buzzserver || true

echo "Deleting containers..."
docker rm buzzserver || true

sleep 1

echo "Starting server container..."
docker run --env-file server/env.env -d -p 14532:80 --net buzz --name buzzserver buzzserver:latest
set +x

echo "To see logs of server, type 'docker logs -f buzzserver'"
echo "View website at http://localhost:14532"
