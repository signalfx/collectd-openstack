#!/usr/bin/env python
import httplib
import json
from time import time, sleep
from subprocess import call

# Quick and dirty integration test for multiple project support for openstack for
# one collectd instance. This test script is intended to be run with
# docker-compose with the provided docker-compose.yml configuration.

# This is not very flexible but could be expanded to support other types of
# integration tests if so desired.

OPENSTACK_HOSTS = [
    'openstack',
]
TIMEOUT_SECS = 180


def get_metric_data():
    # Use httplib instead of requests so we don't have to install stuff with pip
    conn = httplib.HTTPConnection("fake_sfx", 8080)
    conn.request("GET", "/")
    resp = conn.getresponse()
    a = resp.read()
    return json.loads(a)


def wait_for_metrics():
    start = time()
    plugin = 'openstack'

    print "waiting for metrics from plugin {0}".format(plugin)
    eventually_true(lambda: any([plugin in m.get('plugin').split(':')[0] for m in get_metric_data()]),
                    TIMEOUT_SECS - (time() - start))
    print 'Found!'


def eventually_true(f, timeout_secs):
    start = time()
    while True:
        try:
            assert f()
        except AssertionError:
            if time() - start > timeout_secs:
                raise
            sleep(1)
        else:
            break


if __name__ == "__main__":
    wait_for_metrics()
