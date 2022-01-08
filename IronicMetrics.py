from concurrent.futures import ThreadPoolExecutor
import re

from keystoneauth1 import identity
from keystoneauth1 import session
from ironicclient import client
import pprint
### TEMP IMPORT FOR TESTING ##
from pprint import pprint


METRIC_NAME_PREFIX = "openstack."
IRONIC_HYPERVISOR_PREFIX = "ironic.hypervisor."
#IRONIC_LIMIT_PREFIX = "ironic.limit."
DEFAULT_IRONIC_CLIENT_VERSION = "1"

IRONIC_HYPERVISOR_METRICS = [
    "uuid",
    "name",
    "instance_uuid",
    "power_state",
    "provisioning_state",
    "maintenance",
    "service_id",
    "state",
    "status"


]

IRONIC_HYPERVISOR_DIMS = [
    "uuid"
]

IRONIC_HYPERVISOR_PROPS = [
    "hypervisor_hostname"
]








class IronicMetrics:
    def __init__(
        self,
        auth_url,
        username,
        password,
        project_name,
        project_domain_id,
        user_domain_id,
        region_name,
        ssl_verify,
        http_timeout,
        request_batch_size,
        list_servers_search_opts={},
    ):
        self._auth_url = auth_url
        self._username = username
        self._password = password
        self._project_name = project_name
        self._project_domain_id = project_domain_id
        self._user_domain_id = user_domain_id
        self._region_name = region_name
        self._ssl_verify = ssl_verify
        self._tpe = ThreadPoolExecutor(request_batch_size)
        self._list_servers_search_opts = list_servers_search_opts

        self.auth = identity.Password(
            auth_url=self._auth_url,
            username=self._username,
            password=self._password,
            project_name=self._project_name,
            project_domain_id=self._project_domain_id,
            user_domain_id=self._user_domain_id
        )
        self.sess = session.Session(auth=self.auth, verify=self._ssl_verify, timeout=http_timeout)
        self.ironic = client.Client(
            DEFAULT_IRONIC_CLIENT_VERSION,
            session=self.sess,
            region_name=self._region_name,
        )

    def _build_hypervisor_metrics(self, hypervisorId):
        metrics = []
        dims = {}
        props = {}

        try:
            hypervisor = self.ironic.node.get(hypervisorId)

        except Exception:
            # In case of error, do nothing
            hypervisor = None
        

        # Create metrics
        for metric in IRONIC_HYPERVISOR_METRICS:
            metricValue = getattr(hypervisor, metric, None)

            if metricValue is not None :
                if isinstance(metricValue,(float, int, str)):
                    metricValue = metricValue
                    print(metricValue + "is not Bool")
                elif  not isinstance(metricValue, (float, int, str)):
                    metricValue = str(metricValue)
                    print(str(metricValue) + "is Bool")
                metrics.append(("{0}{1}{2}".format(
                    METRIC_NAME_PREFIX,
                    IRONIC_HYPERVISOR_PREFIX,
                    metric
                ),

                metricValue))


        # Pull dimensions
        for dim in IRONIC_HYPERVISOR_DIMS:
            dimValue = getattr(hypervisor, dim, None)

            if dimValue is not None:
                dims[dim] = dimValue



        # Pull properties
        for prop in IRONIC_HYPERVISOR_PROPS:
            propValue = getattr(hypervisor, prop, None)

            if propValue is not None:
                props[prop] = propValue

        props["project_name"] = self._project_name
        props["project_domain_name"] = self._project_domain_id
        props["user_domain_name"] = self._user_domain_id


        return (metrics, dims, props)

    def collect_hypervisor_metrics(self):
        hypervisorList = self.ironic.node.list()

        hypervisorMetrics = {}

        for hypervisor in hypervisorList:
            hypervisorMetrics[hypervisor.uuid] = self._build_hypervisor_metrics(
                hypervisor.uuid
            )

        return hypervisorMetrics
        #return hypervisorList







