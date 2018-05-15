import sys
from os import path
import inspect

from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.neutron import client
import re

METRIC_NAME_PREFIX = "openstack."
NEUTRON_NETWORK_PREFIX = "neutron.network."
NEUTRON_SUBNET_PREFIX = "neutron.subnet."
NEUTRON_ROUTER_PREFIX = 'neutron.router.'
NEUTRON_FLOATIP_PREFIX = 'neutron.floatingip.'
NEUTRON_SG_PREFIX = 'neutron.securitygroup.'
DEFAULT_NEUTRON_CLIENT_VERSION = "2.0"


class NeutronMetrics:
    def __init__(
        self,
        auth_url,
        username,
        password,
        project_name,
        project_domain_id,
        user_domain_id
    ):
        self._auth_url = auth_url
        self._username = username
        self._password = password
        self._project_name = project_name
        self._project_domain_id = project_domain_id
        self._user_domain_id = user_domain_id

        self.auth = identity.Password(
            auth_url=self._auth_url,
            username=self._username,
            password=self._password,
            project_name=self._project_name,
            project_domain_id=self._project_domain_id,
            user_domain_id=self._user_domain_id
        )
        self.sess = session.Session(auth=self.auth)
        self.neutron = client.Client(
            DEFAULT_NEUTRON_CLIENT_VERSION,
            session=self.sess
        )

    def collect_neutron_metrics(self):
        metrics = []
        dims = {}
        props = {}

        self.collect_network_metrics(metrics)
        self.collect_subnet_metrics(metrics)
        self.collect_router_metrics(metrics)
        self.collect_floatingip_metrics(metrics)
        self.collect_sg_metrics(metrics)

        props["project_name"] = self._project_name
        props["project_domain_name"] = self._project_domain_id
        props["user_domain_name"] = self._user_domain_id

        return {'0': (metrics, dims, props)}

    def collect_network_metrics(self, metrics):
        networks = self.neutron.list_networks()['networks']

        data_tenant = dict()
        data_tenant['network'] = {'count': 0}

        for network in networks:
            data_tenant['network']['count'] += 1

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                NEUTRON_NETWORK_PREFIX,
                'count'
            ), data_tenant['network']['count']))

    def collect_subnet_metrics(self, metrics):
        subnets = self.neutron.list_subnets()['subnets']

        data_tenant = dict()
        data_tenant['subnet'] = {'count': 0}

        for subnet in subnets:
            data_tenant['subnet']['count'] += 1

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                NEUTRON_SUBNET_PREFIX,
                'count'
            ), data_tenant['subnet']['count']))

    def collect_router_metrics(self, metrics):
        routers = self.neutron.list_routers()['routers']

        data_tenant = dict()
        data_tenant['router'] = {'count': 0}

        for router in routers:
            data_tenant['router']['count'] += 1

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                NEUTRON_ROUTER_PREFIX,
                'count'
            ), data_tenant['router']['count']))

    def collect_floatingip_metrics(self, metrics):
        floatingips = self.neutron.list_floatingips()['floatingips']

        data_tenant = dict()
        data_tenant['floatingip'] = {'count': 0}

        for floatingip in floatingips:
            data_tenant['floatingip']['count'] += 1

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                NEUTRON_FLOATIP_PREFIX,
                'count'
            ), data_tenant['floatingip']['count']))

    def collect_sg_metrics(self, metrics):
        sgs = self.neutron.list_security_groups()['security_groups']

        data_tenant = dict()
        data_tenant['sg'] = {'count': 0}

        for sg in sgs:
            data_tenant['sg']['count'] += 1

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                NEUTRON_SG_PREFIX,
                'count'
            ), data_tenant['sg']['count']))

