#!/bin/bash -ex

docker build -t devstack:builder .
docker run -d --privileged \
    --name devstack \
    -v /lib/modules:/lib/modules:ro \
    -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
    -e container=docker \
    devstack:builder

docker exec devstack systemctl start devstack
docker exec devstack systemctl stop devstack

docker export -o /tmp/devstack.tar devstack
# entrypoint doesn't seem to persist for all exports
docker import -c 'ENTRYPOINT ["/lib/systemd/systemd"]' /tmp/devstack.tar devstack:latest

docker rm -fv devstack
docker rmi devstack:builder
rm -f /tmp/devstack.tar
