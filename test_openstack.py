#!/usr/bin/env python
import collections
import mock
import sys
import pytest
import sample_responses
import openstack_metrics


class MockCollectd(mock.MagicMock):

    @staticmethod
    def log(log_str):
        print log_str

    debug = log
    info = log
    warning = log
    error = log

sys.modules['collectd'] = MockCollectd()


def mock_api_call(url):
    if 'nova' in url:
        return sample_responses.nova_metrics

    if 'cinder' in url:
        return sample_responses.cinder_metrics

    if 'neutron' in url:
        return sample_responses.neutron_metrics


ConfigOption = collections.namedtuple('ConfigOption', ('key', 'values'))

fail_mock_config_required_params = mock.Mock()
fail_mock_config_required_params.children = [
    ConfigOption('AuthURL', ('http://localhost/identity/v3',)),
    ConfigOption('Testing', ('True'))
]


def test_config_fail():
    with pytest.raises(KeyError):
        openstack_metrics.config_callback(fail_mock_config_required_params)


mock_config = mock.Mock()
mock_config.children = [
    ConfigOption('AuthURL', ('http://localhost/identity/v3', )),
    ConfigOption('Username', ('admin', )),
    ConfigOption('Password', ('secret', )),
    ConfigOption('ProjectName', ('demo', )),
    ConfigOption('ProjectDomainId', ('default', )),
    ConfigOption('UserDomainId', ('default', )),
    ConfigOption('Testing', ('True', )),
]


def test_default_config():
    module_config = openstack_metrics.config_callback(mock_config)
    assert module_config['authurl'] == 'http://localhost/identity/v3'
    assert module_config['username'] == 'admin'
    assert module_config['password'] == 'secret'


@mock.patch('openstack_metrics._api_call', mock_api_call)
def test_with_default_metrics():
    openstack_metrics.read_callback(openstack_metrics.config_callback(mock_config))
