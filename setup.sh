#!/bin/bash

export BASE_DIR=$(pwd)

if [[ ! -f "${BASE_DIR}/setup.sh" ]];
then
  echo "~~~~~~"
  echo "FAILED"
  echo "~~~~~~"
  echo "Please source setup.sh from the buzz/ directory"
  printf "\tcd buzz && source setup.sh\n"
  return 1
fi

cp git-hook-src/pre-push .git/hooks/pre-push

python3 -m venv venv

. venv/bin/activate

pip install -r server/requirements.txt

