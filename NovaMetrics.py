import sys
from os import path
import inspect

from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client
import re

METRIC_NAME_PREFIX = "openstack."
NOVA_HYPERVISOR_PREFIX = "nova.hypervisor."
NOVA_SERVER_PREFIX = "nova.server."
NOVA_LIMIT_PREFIX = "nova.limit."
DEFAULT_NOVA_CLIENT_VERSION = "2.1"

NOVA_HYPERVISOR_METRICS = [
    "current_workload",
    "disk_available_least",
    "free_disk_gb",
    "free_ram_mb",
    "local_gb",
    "local_gb_used",
    "memory_mb",
    "memory_mb_used",
    "running_vms",
    "vcpus",
    "vcpus_used"
]

NOVA_HYPERVISOR_DIMS = [
    "id"
]

NOVA_HYPERVISOR_PROPS = [
    "cpu_info_model",
    "cpu_info_vendor",
    "host_ip",
    "hypervisor_type",
    "hypervisor_version",
    "service_host",
    "service_id",
    "state",
    "status",
    "hypervisor_hostname",
]

NOVA_HYPERVISOR_UPTIME_METRICS = [
    "uptime"
]

NOVA_SERVER_DIAG_METIRCS = [
    "cpu0_time",
    "cpu1_time",
    "memory",
    "memory-actual",
    "memory-rss",
    "vda_errors",
    "vda_read",
    "vda_read_req",
    "vda_write",
    "vda_write_req",
    "hdd_read",
    "hdd_write",
    "hdd_errors",
    "hdd_read_req",
    "hdd_write_req",
    "rx",
    "rx_drop",
    "rx_packets",
    "tx",
    "tx_drop",
    "tx_packets"
]

NOVA_SERVER_DIMS = [
    "id",
]

NOVA_SERVER_PROPS = [
    "status",
    "user_id",
    "hostId",
    "flavor",
    "OS-EXT-AZ:availability_zone",
    "OS-EXT-SRV-ATTR:hypervisor_hostname",
    "OS-EXT-SRV-ATTR:hostname",
    "OS-EXT-SRV-ATTR:instance_name"
]

NOVA_LIMIT_METRICS = [
    "maxImageMeta",
    "maxSecurityGroups",
    "maxTotalCores",
    "maxTotalFloatingIps",
    "maxTotalInstances",
    "maxTotalKeypairs",
    "maxTotalRAMSize",
    "totalCoresUsed",
    "totalFloatingIpsUsed",
    "totalInstancesUsed",
    "totalRAMUsed",
    "totalSecurityGroupsUsed"
]


class NovaMetrics:
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
        self.nova = client.Client(
            DEFAULT_NOVA_CLIENT_VERSION,
            session=self.sess
        )

    def _build_hypervisor_metrics(self, hypervisorId):
        metrics = []
        dims = {}
        props = {}

        try:
            hypervisor = self.nova.hypervisors.get(hypervisorId)
            uptime = self.nova.hypervisors.uptime(hypervisorId)
        except Exception:
            # In case of error, do nothing
            hypervisor = None
            uptime = None

        # Create metrics
        for metric in NOVA_HYPERVISOR_METRICS:
            metricValue = getattr(hypervisor, metric, None)

            if metricValue is not None:
                metrics.append(("{0}{1}{2}".format(
                    METRIC_NAME_PREFIX,
                    NOVA_HYPERVISOR_PREFIX,
                    metric
                ), metricValue))

        for uptimeMetric in NOVA_HYPERVISOR_UPTIME_METRICS:
            uptimeValue = getattr(uptime, uptimeMetric, None)

            if uptimeValue is not None:
                if uptimeMetric == "uptime":
                    reLoadAvg = re.search(
                        "load average: ([0-9.]+), ([0-9.]+), ([0-9.]+)",
                        uptimeValue
                    )
                    metrics.append(("{0}{1}load_average_1m".format(
                        METRIC_NAME_PREFIX,
                        NOVA_HYPERVISOR_PREFIX
                    ), reLoadAvg.group(1)))
                    metrics.append(("{0}{1}load_average_5m".format(
                        METRIC_NAME_PREFIX,
                        NOVA_HYPERVISOR_PREFIX
                    ), reLoadAvg.group(2)))
                    metrics.append(("{0}{1}load_average_15m".format(
                        METRIC_NAME_PREFIX,
                        NOVA_HYPERVISOR_PREFIX
                    ), reLoadAvg.group(3)))

        # Pull dimensions
        for dim in NOVA_HYPERVISOR_DIMS:
            dimValue = getattr(hypervisor, dim, None)

            if dimValue is not None:
                dims[dim] = dimValue

        # Pull properties
        for prop in NOVA_HYPERVISOR_PROPS:
            propValue = getattr(hypervisor, prop, None)

            if propValue is not None:
                props[prop] = propValue

        dims["project_id"] = self.nova.client.get_project_id()
        props["project_name"] = self._project_name
        props["project_domain_name"] = self._project_domain_id
        props["user_domain_name"] = self._user_domain_id

        return (metrics, dims, props)

    def _build_server_metrics(self, serverId):
        metrics = []
        dims = {}
        props = {}

        try:
            server = self.nova.servers.get(serverId)
            serverDiagnostics = server.diagnostics()[1]
        except Exception:
            # In case of error, do nothing
            server = None
            serverDiagnostics = {}

        # Create metrics
        diagNetworkMetrics = (
            "rx",
            "rx_drop",
            "rx_packets",
            "tx",
            "tx_drop",
            "tx_packets"
        )

        for diagMetric in NOVA_SERVER_DIAG_METIRCS:
            diagValue = None

            # Sum up network stats since they are reported per network device
            if diagMetric in diagNetworkMetrics:
                attrs = serverDiagnostics.keys()
                for a in attrs:
                    if a.endswith(diagMetric):
                        tmpValue = serverDiagnostics.get(a, 0)
                        if diagValue is not None:
                            diagValue += tmpValue
                        else:
                            diagValue = tmpValue
            else:
                diagValue = serverDiagnostics.get(diagMetric, None)

            if diagValue is not None:
                metrics.append(("{0}{1}{2}".format(
                    METRIC_NAME_PREFIX,
                    NOVA_SERVER_PREFIX,
                    diagMetric
                ), diagValue))

        # Pull dimensions
        for dim in NOVA_SERVER_DIMS:
            dimValue = getattr(server, dim, None)

            if dimValue is not None:
                dims[dim] = dimValue

        # Pull properties
        for prop in NOVA_SERVER_PROPS:
            propValue = None
            if prop == "flavor":
                tmpValue = getattr(server, "flavor", None)
                if tmpValue is not None:
                    flavor = self.nova.flavors.get(tmpValue["id"])
                    flavorName = getattr(flavor, "name", None)
                    if flavorName is not None:
                        propValue = flavorName
            else:
                propValue = getattr(server, prop, None)

            if propValue is not None:
                propName = prop
                if prop.startswith("OS-EXT"):
                    propName = prop.split(":")[1]

                props[propName] = propValue

        dims["project_id"] = self.nova.client.get_project_id()
        props["project_name"] = self._project_name
        props["project_domain_name"] = self._project_domain_id
        props["user_domain_name"] = self._user_domain_id

        return (metrics, dims, props)

    def collect_hypervisor_metrics(self):
        hypervisorList = self.nova.hypervisors.list()

        hypervisorMetrics = {}

        for hypervisor in hypervisorList:
            hypervisorMetrics[hypervisor.id] = self._build_hypervisor_metrics(
                hypervisor.id
            )

        return hypervisorMetrics

    def collect_server_metrics(self):
        serverList = self.nova.servers.list()

        serverMetrics = {}

        for server in serverList:
            serverMetrics[server.id] = self._build_server_metrics(server.id)

        return serverMetrics

    def collect_limit_metrics(self):
        limits = self.nova.limits.get().to_dict()['absolute']

        metrics = []
        dims = {}
        props = {}

        for metric in NOVA_LIMIT_METRICS:
            metricValue = limits.get(metric, None)

            if metricValue is not None:
                metrics.append(("{0}{1}{2}".format(
                    METRIC_NAME_PREFIX,
                    NOVA_LIMIT_PREFIX,
                    metric
                ), metricValue))

        dims["project_id"] = self.nova.client.get_project_id()
        props["project_name"] = self._project_name
        props["project_domain_name"] = self._project_domain_id
        props["user_domain_name"] = self._user_domain_id

        return {'0': (metrics, dims, props)}
