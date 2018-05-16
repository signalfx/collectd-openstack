import sys
from os import path
import inspect

from keystoneauth1 import identity
from keystoneauth1 import session
from cinderclient import client
import re

METRIC_NAME_PREFIX = "openstack."
CINDER_LIMIT_PREFIX = "cinder.limit."
CINDER_VOLUME_PREFIX = "cinder.volume."
CINDER_SNAPSHOT_PREFIX = "cinder.snapshot."
DEFAULT_CINDER_CLIENT_VERSION = "2.0"


class CinderMetrics:
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
        self.cinder = client.Client(
            DEFAULT_CINDER_CLIENT_VERSION,
            session=self.sess
        )

    def collect_cinder_metrics(self):
        metrics = []
        dims = {}
        props = {}

        self.collect_volume_metrics(metrics)
        self.collect_snapshot_metrics(metrics)
        self.collect_limit_metrics(metrics)

        dims["project_id"] = self.cinder.client.get_project_id()
        props["project_name"] = self._project_name
        props["project_domain_name"] = self._project_domain_id
        props["user_domain_name"] = self._user_domain_id

        return {'0': (metrics, dims, props)}

    def collect_volume_metrics(self, metrics):
        volumes = self.cinder.volumes.list(search_opts={'all_tenants': 1})

        data_tenant = dict()
        data_tenant['volumes'] = {'count': 0, 'bytes': 0}

        for volume in volumes:
            data_tenant['volumes']['count'] += 1
            data_tenant['volumes']['bytes'] += (volume.size * 1024 * 1024 * 1024)

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                CINDER_VOLUME_PREFIX,
                'count'
            ), data_tenant['volumes']['count']))
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                CINDER_VOLUME_PREFIX,
                'size'
            ), data_tenant['volumes']['bytes']))

    def collect_snapshot_metrics(self, metrics):
        snapshots = self.cinder.volume_snapshots.list(search_opts={'all_tenants': 1})

        data_tenant = dict()
        data_tenant['snapshot'] = {'count': 0, 'bytes': 0}

        for snapshot in snapshots:
            data_tenant['snapshot']['count'] += 1
            data_tenant['snapshot']['bytes'] += (snapshot.size * 1024 * 1024 * 1024)

        if data_tenant is not None:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                CINDER_SNAPSHOT_PREFIX,
                'count'
            ), data_tenant['snapshot']['count']))
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                CINDER_SNAPSHOT_PREFIX,
                'size'
            ), data_tenant['snapshot']['bytes']))

    def collect_limit_metrics(self, metrics):
        limits = self.cinder.limits.get().to_dict()['absolute']

        for limit in limits:
            metrics.append(("{0}{1}{2}".format(
                METRIC_NAME_PREFIX,
                CINDER_LIMIT_PREFIX,
                limit
            ), limits[limit]))
