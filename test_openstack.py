#!/usr/bin/env python
from http.server import BaseHTTPRequestHandler, HTTPServer
import collections
import sys
from threading import Thread

import mock
import pytest


def import_module():
    class MockCollectd(mock.MagicMock):
        @staticmethod
        def log(log_str):
            print(log_str)

        debug = log
        info = log
        warning = log
        error = log

    sys.modules["collectd"] = MockCollectd()

    import openstack_metrics

    return openstack_metrics


openstack_metrics = import_module()

identity = """{"version": {
    "id": "v3.12",
    "links": [{"href": "http://127.0.0.1:8080/identity/v3/", "rel": "self"}],
    "media-types": [{"base": "application/json", "type": "application/vnd.openstack.identity-v3+json"}],
    "status": "stable",
    "updated": "2019-01-22T00:00:00Z"
}}"""

tokens = """ { "token": { "audit_ids": [ "slVNmR4lRXaBjptrqGQWYA" ], "catalog": [ { "endpoints": [ { "id": "e29bbfebedc34b96890e2e1d72907cae", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/" } ], "id": "0fee659b840e44f49f1da2a859dbff1c", "name": "neutron", "type": "network" }, { "endpoints": [ { "id": "06944393f2e0405f9a26874dddd69bfe", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/volume/v3/0b67f1ab39f14260b08a017011b3e3e6" } ], "id": "4540653a4874418b8da6df25b8d005f5", "name": "cinder", "type": "block-storage" }, { "endpoints": [ { "id": "4739cb9faa1742b39a40b65b4eba5b79", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/identity" }, { "id": "d0e90d368aa542cbbf861d61cff44331", "interface": "admin", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/identity" } ],
                "id": "725275caac834fd486d2665771c39de5", "name": "keystone", "type": "identity" }, { "endpoints": [ { "id": "54add0a0d2c54b16a0753e12da1ba3fc", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/compute/v2/0b67f1ab39f14260b08a017011b3e3e6" } ], "id": "7eace5558c75472d866ad260489b406e",
                "name": "nova_legacy", "type": "compute_legacy" }, { "endpoints": [ { "id": "34803e9725d342dfb039b2efb594a13e", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/compute/v2.1" } ], "id": "83f111432c11490d942758e432bd2fad",
                "name": "nova", "type": "compute" }, { "endpoints": [ { "id": "9079570034e94ed99d7ce826f35e58e8", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/placement" } ], "id": "887ba156b0d548cd90d31d9e4d067376",
                "name": "placement", "type": "placement" }, { "endpoints": [ { "id": "5a55f7df5bb448f7816c6441ea483e50", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/volume/v2/0b67f1ab39f14260b08a017011b3e3e6" } ], "id": "8d711b5c719c49099e5ee3720c448ce6", "name": "cinderv2",
                "type": "volumev2" }, { "endpoints": [ { "id": "988314367a1448da88a3396482fde4e1", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/volume/v3/0b67f1ab39f14260b08a017011b3e3e6" } ], "id": "a39cb09c524741f492bcd8135ce720c6",
                "name": "cinderv3", "type": "volumev3" }, { "endpoints": [ { "id": "64ebb125fff242b18ff58e4b47e27e14", "interface": "public", "region": "RegionOne", "region_id": "RegionOne", "url": "http://127.0.0.1:8080/image" } ], "id": "febb4bd9b64c45ce81a57974357d9e1f",
                "name": "glance", "type": "image" } ], "expires_at": "2025-09-09T00:01:31.000000Z", "is_domain": false, "issued_at": "2021-09-08T23:01:31.000000Z", "methods": [ "password" ], "project": { "domain": { "id": "default", "name": "Default" }, "id": "0b67f1ab39f14260b08a017011b3e3e6", "name": "demo"
        }, "roles": [ { "id": "867ec0c2b4454179bbf0abe0dd258eb8", "name": "admin" }, { "id": "d97ed88767ac4e4290cf8e190c8ac8b8", "name": "reader" }, { "id": "dfeb24871124450bb2ec15a2e899b7e3", "name": "member" } ],
        "user": { "domain": { "id": "default", "name": "Default" }, "id": "ea6d7f93aa7a43e8b8e9088046801a5c", "name": "admin", "password_expires_at": null } } } """

search_opts_sourced = False

class MockOpenstack(BaseHTTPRequestHandler):
    def do_GET(self):
        response = ""
        if self.path == "/identity/v3":
            response = identity
        if "/compute/v2.1/servers/detail" in self.path:
            if self.path == "/compute/v2.1/servers/detail?all_tenants=TRUE&status=ACTIVE":
                global search_opts_sourced
                search_opts_sourced = True
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(bytes(response, "utf-8"))

    def do_POST(self):
        response = ""
        self.send_response(200)
        if self.path == "/identity/v3/auth/tokens":
            response = tokens
            self.send_header('X-Subject-Token', "gAAAAABhOUDLATJ_3XdR-x3DamEABFcpcBJW8mOUhSC_OoJ0-GeqKrNm8746m3H_1bK2iRvVYrxi28Y0CojHQVhoRit8IF0n43QsjWg1LBgwV8tgUUtCvDa9zhUB7mBqg3sEPudGtVzZVQc1wwCmlDGDCg9uP_iRAzfBq78eTGby_-eAVuAGeOk")

        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(bytes(response, "utf-8"))


ConfigOption = collections.namedtuple("ConfigOption", ("key", "values"))


def test_config_fail():
    fail_mock_config_required_params = mock.Mock()
    fail_mock_config_required_params.children = [
        ConfigOption("Testing", (True,)),
        ConfigOption("AuthURL", ("http://localhost/identity/v3",)),
    ]

    with pytest.raises(KeyError):
        openstack_metrics.config_callback(fail_mock_config_required_params)


def test_default_config():
    mock_config = mock.Mock()
    mock_config.children = [
        ConfigOption("Testing", (True,)),
        ConfigOption("AuthURL", ("http://localhost/identity/v3",)),
        ConfigOption("Username", ("admin",)),
        ConfigOption("Password", ("secret",)),
        ConfigOption("ProjectName", ("demo",)),
        ConfigOption("ProjectDomainId", ("default",)),
        ConfigOption("UserDomainId", ("default",)),
        ConfigOption("Interval", (100,)),
        ConfigOption("SSLVerify", (True,)),
        ConfigOption("HTTPTimeout", (123.456,)),
        ConfigOption("RequestBatchSize", (100,)),
        ConfigOption("QueryServerMetrics", (True,)),
        ConfigOption("NovaListServersSearchOpts", ('{}',)),
    ]

    module_config, clients = openstack_metrics.config_callback(mock_config)
    assert module_config["authurl"] == "http://localhost/identity/v3"
    assert module_config["username"] == "admin"
    assert module_config["password"] == "secret"
    for client in ["neutron", "nova", "cinder"]:
        assert clients[client].sess.timeout == 123.456

    assert clients["nova"]._list_servers_search_opts == {}


@pytest.fixture()
def mock_openstack():
    httpd = HTTPServer(("", 8080), MockOpenstack)
    thread = Thread(target=httpd.serve_forever)
    thread.setDaemon(True)
    thread.start()
    yield
    httpd.shutdown()
    thread.join()

def test_with_default_metrics(mock_openstack):
    mock_config = mock.Mock()
    mock_config.children = [
        ConfigOption("Testing", (True,)),
        ConfigOption("AuthURL", ("http://localhost:8080/identity/v3",)),
        ConfigOption("Username", ("admin",)),
        ConfigOption("Password", ("secret",)),
        ConfigOption("ProjectName", ("demo",)),
        ConfigOption("ProjectDomainId", ("default",)),
        ConfigOption("UserDomainId", ("default",)),
        ConfigOption("Interval", (100,)),
        ConfigOption("SSLVerify", (True,)),
        ConfigOption("HTTPTimeout", (123.456,)),
        ConfigOption("RequestBatchSize", (100,)),
        ConfigOption("QueryServerMetrics", (True,)),
        ConfigOption("NovaListServersSearchOpts", ('{ all_tenants: "TRUE", status: "ACTIVE" }',)),
    ]

    print("Starting metric spewer on port 8080")
    print("Metric spewer shutting down")

    _, clients = openstack_metrics.config_callback(mock_config)

    assert clients["nova"]._list_servers_search_opts == {"all_tenants": "TRUE", "status": "ACTIVE"}

    openstack_metrics.read_callback(clients)

    assert search_opts_sourced
