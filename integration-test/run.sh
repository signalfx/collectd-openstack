#!/bin/bash
echo "Be sure that you have run devstack/make-devstack-image.sh before trying this."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

echo "Running tests"
docker-compose run --rm test
status=$?

docker-compose down

exit $status
