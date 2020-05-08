#!/bin/bash

set -e

echo "Stopping containers..."

docker kill buzzdb buzzserver || true

echo "Deleting containers..."
docker rm buzzdb buzzserver || true

echo "Deleting network..."
docker network prune -f

echo "done"
