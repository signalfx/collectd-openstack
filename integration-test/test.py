#!/usr/bin/env python
import http.client
import json
from time import time, sleep


# Use httplib to avoid dependencies
def get(host, port, endpoint):
    try:
        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", endpoint)
        return json.loads(conn.getresponse().read())
    except:
        return {}


def get_metric_data():
    received = get("fake_sfx", 8080, "/")
    if len(received):
        print("received: {0}".format(received))
    return received


def wait_for_openstack():
    print("waiting to be able to reach openstack")
    eventually_true(lambda: len(get("devstack", 80, "/compute")) > 0, 1800)
    print("Openstack is accessible.")


def wait_for_metrics():
    print("waiting for metrics from plugin openstack")
    eventually_true(lambda: any(["openstack" in m.get('plugin').split(':')[0] for m in get_metric_data()]), 500)
    print('Found!')


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
    wait_for_openstack()
    # takes a long time for openstack to become accessible after compute endpoint
    print("sleeping for 10m")
    sleep(600)
    wait_for_metrics()
