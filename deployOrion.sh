#!/bin/bash

echo "Pushing db"

docker save buzzdb:latest | \
  bzip2 | \
  ssh hugo@blog.hugo-klepsch.tech 'bunzip2 | docker load'

echo "done"

echo "Pushing server"

docker save buzzserver:latest | \
  bzip2 | \
  ssh hugo@blog.hugo-klepsch.tech 'bunzip2 | docker load'

echo "done"

echo "Push start.sh"
cat start.sh | \
  bzip2 | \
  ssh hugo@blog.hugo-klepsch.tech \
    'bunzip2 > /home/hugo/buzz/start.sh && chmod u+x /home/hugo/buzz/start.sh'

echo "done"

echo "Push stop.sh"
cat stop.sh | \
  bzip2 | \
  ssh hugo@blog.hugo-klepsch.tech \
    'bunzip2 > /home/hugo/buzz/stop.sh && chmod u+x /home/hugo/buzz/stop.sh'

echo "done"
